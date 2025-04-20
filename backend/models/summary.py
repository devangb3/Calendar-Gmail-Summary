from datetime import datetime, timedelta
from config.database import Database

class Summary:
    def __init__(self, user_id, summary_text, prompt_used=None):
        self.user_id = user_id
        self.summary_text = summary_text
        self.prompt_used = prompt_used
        self.generated_at = datetime.utcnow()
        self.db = Database.get_instance()

    def save(self):
        if self.db is None or not self.db.is_connected():
            raise Exception("Database not connected")
        
        summary_doc = {
            "user_id": self.user_id,
            "summary_text": self.summary_text,
            "generated_at": self.generated_at,
            "prompt_used": self.prompt_used
        }
        return self.db.summaries.insert_one(summary_doc)

    @staticmethod
    def get_recent_summary(user_id, hours=1):
        db = Database.get_instance()
        if db is None or not db.is_connected():
            return None
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        cached_summary = db.summaries.find_one(
            {
                'user_id': user_id, 
                'generated_at': {'$gte': cutoff_time}
            },
            sort=[('generated_at', -1)]
        )
        
        if cached_summary:
            summary = Summary(
                user_id=cached_summary['user_id'],
                summary_text=cached_summary['summary_text'],
                prompt_used=cached_summary.get('prompt_used')
            )
            summary.generated_at = cached_summary['generated_at']
            return summary
        
        return None