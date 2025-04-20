from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta, timezone
import asyncio
from models.user import User
from models.summary import Summary
from services.calendar_service import CalendarService
from services.gmail_service import GmailService
from services.gemini_service import GeminiService
from utils.logger import summary_logger, log_error
from config.database import Database

class SingletonException(Exception):
    """Exception raised when attempting to create multiple instances of a singleton."""
    pass

class SchedulerService:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if SchedulerService._instance is not None:
            raise SingletonException("SchedulerService is a singleton!")
            
        self.scheduler = BackgroundScheduler()
        self.gemini_service = GeminiService()
        self.db = Database.get_instance()
        self.loop = asyncio.get_event_loop()
        
    def start(self):
        """Start the scheduler"""
        try:
            # Add the refresh digest job to run every 60 minutes
            self.scheduler.add_job(
                func=self._refresh_all_digests,
                trigger=IntervalTrigger(minutes=60),
                id='refresh_digests',
                name='Refresh user digests',
                replace_existing=True
            )
            
            self.scheduler.start()
            summary_logger.info("Scheduler started successfully")
        except Exception as e:
            log_error(summary_logger, e, "Failed to start scheduler")
            raise
            
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        summary_logger.info("Scheduler stopped")

    def refresh_user_digest(self, user_id):
        """Refresh digest for a single user synchronously"""
        return asyncio.run(self._refresh_user_digest_async(user_id))
            
    async def _refresh_user_digest_async(self, user_id):
        """Refresh digest for a single user"""
        try:
            summary_logger.info(f"Refreshing digest for user: {user_id}")
            
            # Get user and check credentials
            user = User.find_by_id(user_id)
            if not user or not user.credentials:
                summary_logger.warning(f"User {user_id} not found or has no credentials")
                return
                
            # Initialize services
            calendar_service = CalendarService(user.credentials)
            gmail_service = GmailService(user.credentials)
            
            # Fetch data
            events = calendar_service.get_events(
                time_min=datetime.now(timezone.utc).isoformat(),
                time_max=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
            )
            emails = gmail_service.get_recent_emails(max_results=5)
            
            # Generate summary
            summary_text = self.gemini_service.generate_summary(events, emails)
            
            # Save to database
            summary = Summary(user_id, summary_text)
            summary.save()
            
            summary_logger.info(f"Successfully refreshed digest for user: {user_id}")
            return {
                "summary": summary_text,
                "emails": emails,
                "events": events,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            log_error(summary_logger, e, f"Failed to refresh digest for user: {user_id}")
            raise
            
    def _refresh_all_digests(self):
        """Refresh digests for all users with valid credentials"""
        try:
            summary_logger.info("Starting bulk digest refresh")
            
            # Get all users from database
            if not self.db.is_connected():
                summary_logger.error("Database not connected")
                return
                
            users_cursor = self.db.users.find({
                "credentials": {"$exists": True, "$ne": None}
            })
            
            for user_data in users_cursor:
                try:
                    user = User(user_data['user_id'], user_data.get('email'), user_data.get('name', ''))
                    self.refresh_user_digest(user.user_id)
                except Exception as e:
                    log_error(summary_logger, e, f"Failed to refresh digest for user: {user_data.get('user_id')}")
                    continue
                    
            summary_logger.info("Completed bulk digest refresh")
            
        except Exception as e:
            log_error(summary_logger, e, "Failed to run bulk digest refresh")