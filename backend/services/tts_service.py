import os
from gtts import gTTS
from tempfile import NamedTemporaryFile
import json
from utils.logger import summary_logger, log_error
from services.gemini_service import GeminiService
import atexit

class TTSService:
    def __init__(self):
        self.gemini_service = GeminiService()
        self._temp_files = set()  # Using regular set instead of WeakSet
        atexit.register(self._cleanup_temp_files)

    def _cleanup_temp_files(self):
        """Clean up any temporary files on service shutdown"""
        for filepath in list(self._temp_files):  # Create a list to avoid modifying set during iteration
            try:
                if os.path.exists(filepath):
                    os.unlink(filepath)
                self._temp_files.remove(filepath)
            except Exception as e:
                summary_logger.warning(f"Failed to cleanup temp file {filepath}: {e}")

    def generate_audio_summary(self, summary_json):
        """Generate an audio summary from the summary JSON data"""
        temp_file = None
        try:
            summary_logger.info("Generating audio summary")
            
            # Parse the summary JSON
            if isinstance(summary_json, str):
                summary_data = json.loads(summary_json)
            else:
                summary_data = summary_json
                
            # Generate a concise script for the audio summary
            script = self._generate_summary_script(summary_data)
            if not script:
                raise ValueError("Failed to generate audio script")
            
            # Create audio file using gTTS
            tts = gTTS(text=script, lang='en', slow=False)
            
            # Create a temporary file with .mp3 extension
            temp_file = NamedTemporaryFile(suffix='.mp3', delete=False)
            self._temp_files.add(temp_file.name)
            
            try:
                tts.save(temp_file.name)
                summary_logger.info("Audio summary generated successfully")
                return temp_file.name
            except Exception as e:
                if temp_file and os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                    self._temp_files.remove(temp_file.name)
                raise ValueError(f"Failed to save audio file: {str(e)}")
                
        except Exception as e:
            log_error(summary_logger, e, "Failed to generate audio summary")
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
                if temp_file.name in self._temp_files:
                    self._temp_files.remove(temp_file.name)
            raise
            
    def _generate_summary_script(self, summary_data):
        """Generate a natural-sounding script for the audio summary"""
        try:
            # Use Gemini to generate a more natural-sounding script
            prompt = f"""Based on this summary data, create a brief, natural-sounding audio script. 
            Make it conversational but professional, and focus on the most important points.
            Include quick overview, priority items, upcoming events, and important emails.
            Keep it under 45 seconds when spoken. Only include what you will say in the audio, do not include any other text.
            Data: {json.dumps(summary_data)}"""
            
            response = self.gemini_service.model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
                
            # Fallback to basic script generation if Gemini fails
            return self._generate_basic_script(summary_data)
            
        except Exception as e:
            summary_logger.warning(f"Failed to generate Gemini script: {str(e)}")
            return self._generate_basic_script(summary_data)
            
    def _generate_basic_script(self, summary_data):
        """Generate a basic script without using Gemini"""
        script_parts = []
        
        # Extract high priority items
        self._add_quick_summary(script_parts, summary_data)
        self._add_priority_events(script_parts, summary_data)
        self._add_important_emails(script_parts, summary_data)
        self._add_urgent_actions(script_parts, summary_data)
                    
        return ". ".join(script_parts)
        
    def _add_quick_summary(self, script_parts, summary_data):
        """Add quick summary to script parts"""
        if 'quickSummary' in summary_data:
            overview = summary_data['quickSummary'].get('overview', '')
            if overview:
                script_parts.append(overview)
                
    def _add_priority_events(self, script_parts, summary_data):
        """Add high priority events to script parts"""
        if not self._has_events(summary_data):
            return
            
        high_priority_events = [
            event for event in summary_data['events']['upcoming']
            if event.get('priority') == 'HIGH'
        ][:2]  # Limit to 2 events
        
        if high_priority_events:
            script_parts.append("High priority events")
            for event in high_priority_events:
                script_parts.append(f"{event['title']} at {event['time']}")
                
    def _add_important_emails(self, script_parts, summary_data):
        """Add important emails to script parts"""
        if not self._has_emails(summary_data):
            return
            
        urgent_emails = [
            email for email in summary_data['emails']['important']
            if email.get('priority') == 'HIGH' or email.get('actionRequired')
        ][:2]  # Limit to 2 emails
        
        if urgent_emails:
            script_parts.append("Important emails requiring attention")
            for email in urgent_emails:
                script_parts.append(f"From {email['from']}, subject: {email['subject']}")
                
    def _add_urgent_actions(self, script_parts, summary_data):
        """Add urgent action items to script parts"""
        if 'actionItems' not in summary_data:
            return
            
        urgent_actions = [
            item for item in summary_data['actionItems']
            if item.get('priority') == 'HIGH'
        ][:2]  # Limit to 2 items
        
        if urgent_actions:
            script_parts.append("Urgent action items")
            for item in urgent_actions:
                script_parts.append(item['task'])
                
    def _has_events(self, summary_data):
        """Check if summary data has valid events"""
        return (
            'events' in summary_data and 
            'upcoming' in summary_data['events'] and 
            isinstance(summary_data['events']['upcoming'], list)
        )
        
    def _has_emails(self, summary_data):
        """Check if summary data has valid emails"""
        return (
            'emails' in summary_data and 
            'important' in summary_data['emails'] and 
            isinstance(summary_data['emails']['important'], list)
        )