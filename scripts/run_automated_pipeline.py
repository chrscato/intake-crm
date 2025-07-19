#!/usr/bin/env python
"""
Automated Email Processing Pipeline
Orchestrates the complete email ingestion and processing workflow.
Designed to run as a cron job for automated processing.
"""
import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add repository root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.settings import settings


class PipelineRunner:
    def __init__(self, config: Dict):
        self.config = config
        self.start_time = datetime.now()
        self.results = {
            "start_time": self.start_time.isoformat(),
            "steps": [],
            "total_emails_processed": 0,
            "total_errors": 0,
            "success": False
        }
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging with both file and console output."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"pipeline_{self.start_time.strftime('%Y%m%d_%H%M%S')}.log"
        
        # Configure logging with UTF-8 encoding for Windows compatibility
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
        # Use Windows-compatible messages
        import sys
        if sys.platform.startswith('win'):
            self.logger.info(f"[STARTING] Automated pipeline at {self.start_time}")
            self.logger.info(f"[LOG] Log file: {log_file}")
        else:
            self.logger.info(f"🚀 Starting automated pipeline at {self.start_time}")
            self.logger.info(f"📝 Log file: {log_file}")
    
    def run_command(self, cmd: List[str], step_name: str, timeout: int = 3600) -> bool:
        """Run a subprocess command with logging and error handling."""
        self.logger.info(f"🔄 Starting step: {step_name}")
        self.logger.info(f"📋 Command: {' '.join(cmd)}")
        
        step_start = datetime.now()
        step_result = {
            "name": step_name,
            "start_time": step_start.isoformat(),
            "command": ' '.join(cmd),
            "success": False,
            "duration_seconds": 0,
            "output": "",
            "error": ""
        }
        
        try:
            # Run the command with proper encoding for Windows
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
                cwd=Path(__file__).parent.parent
            )
            
            step_duration = (datetime.now() - step_start).total_seconds()
            step_result["duration_seconds"] = step_duration
            step_result["output"] = result.stdout
            step_result["error"] = result.stderr
            
            if result.returncode == 0:
                step_result["success"] = True
                self.logger.info(f"✅ {step_name} completed successfully in {step_duration:.1f}s")
                if result.stdout:
                    self.logger.info(f"📤 Output: {result.stdout.strip()}")
            else:
                step_result["success"] = False
                self.results["total_errors"] += 1
                self.logger.error(f"❌ {step_name} failed with return code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"📥 Error: {result.stderr.strip()}")
                if result.stdout:
                    self.logger.info(f"📤 Output: {result.stdout.strip()}")
                    
            return step_result["success"]
            
        except subprocess.TimeoutExpired:
            step_result["error"] = f"Command timed out after {timeout} seconds"
            self.logger.error(f"⏰ {step_name} timed out after {timeout} seconds")
            self.results["total_errors"] += 1
            return False
            
        except Exception as e:
            step_result["error"] = str(e)
            self.logger.error(f"💥 {step_name} failed with exception: {e}")
            self.results["total_errors"] += 1
            return False
            
        finally:
            self.results["steps"].append(step_result)
    
    def step_email_ingestion(self) -> bool:
        """Step 1: Ingest emails from Outlook."""
        cmd = [
            sys.executable, "scripts/run_email_ingestion.py",
            "--max-emails", str(self.config["max_emails"]),
            "--action", "fetch"
        ]
        
        if self.config.get("email_folder"):
            cmd.extend(["--folder", self.config["email_folder"]])
        
        if self.config.get("no_move_emails"):
            cmd.append("--no-move")
            
        return self.run_command(cmd, "Email Ingestion", timeout=1800)  # 30 min timeout
    
    def step_llm_extraction(self) -> bool:
        """Step 2: Extract structured data using LLM."""
        cmd = [
            sys.executable, "scripts/run_llm_extraction.py"
        ]
        
        if self.config.get("extraction_limit"):
            cmd.extend(["--limit", str(self.config["extraction_limit"])])
        
        if self.config.get("resume_extraction"):
            cmd.append("--resume")
            
        if self.config.get("archive_after_extraction"):
            cmd.append("--archive")
        
        return self.run_command(cmd, "LLM Data Extraction", timeout=3600)  # 60 min timeout
    
    def step_geocoding(self) -> bool:
        """Step 3: Geocode patient addresses."""
        if not self.config.get("enable_geocoding", True):
            self.logger.info("⏭️  Skipping geocoding (disabled in config)")
            return True
        
        cmd = [
            sys.executable, "scripts/geocode_addresses.py"
        ]
        
        if self.config.get("geocoding_limit"):
            cmd.extend(["--limit", str(self.config["geocoding_limit"])])
        
        return self.run_command(cmd, "Address Geocoding", timeout=1800)  # 30 min timeout
    
    def step_s3_upload(self) -> bool:
        """Step 4: Upload documents to S3."""
        if not self.config.get("enable_s3_upload", False):
            self.logger.info("⏭️  Skipping S3 upload (disabled in config)")
            return True
        
        cmd = [
            sys.executable, "scripts/upload_docs_to_s3.py"
            # Removed --has-extracted to upload all directories
        ]
        
        if self.config.get("s3_upload_limit"):
            cmd.extend(["--limit", str(self.config["s3_upload_limit"])])
        
        return self.run_command(cmd, "S3 Document Upload", timeout=2400)  # 40 min timeout
    
    def step_database_ingestion(self) -> bool:
        """Step 5: Ingest extracted data into database."""
        if not self.config.get("enable_db_ingestion", True):
            self.logger.info("⏭️  Skipping database ingestion (disabled in config)")
            return True
        
        cmd = [
            sys.executable, "scripts/ingest_to_db.py"
        ]
        
        if self.config.get("db_ingestion_limit"):
            cmd.extend(["--limit", str(self.config["db_ingestion_limit"])])
        
        return self.run_command(cmd, "Database Ingestion", timeout=1800)  # 30 min timeout
    
    def step_cleanup(self) -> bool:
        """Step 6: Archive processed emails."""
        if not self.config.get("enable_cleanup", True):
            self.logger.info("⏭️  Skipping cleanup (disabled in config)")
            return True
        
        cmd = [
            sys.executable, "scripts/archive_processed_emails.py"
        ]
        
        return self.run_command(cmd, "Email Archiving", timeout=600)  # 10 min timeout
    
    def check_prerequisites(self) -> bool:
        """Check that all required environment variables and dependencies are available."""
        self.logger.info("🔍 Checking prerequisites...")
        
        # Check required environment variables
        required_vars = [
            settings.GRAPH_TENANT_ID,
            settings.GRAPH_CLIENT_ID,
            settings.GRAPH_CLIENT_SECRET,
            settings.SHARED_MAILBOX
        ]
        
        if not all(required_vars):
            self.logger.error("❌ Missing required environment variables for Microsoft Graph")
            return False
        
        # Check OpenAI API key for LLM extraction
        if not settings.OPENAI_API_KEY:
            self.logger.error("❌ Missing OPENAI_API_KEY environment variable")
            return False
        
        # Check S3 credentials if S3 upload is enabled
        if self.config.get("enable_s3_upload", False):
            if not all([settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY, settings.S3_BUCKET]):
                self.logger.error("❌ Missing AWS credentials for S3 upload")
                return False
        
        self.logger.info("✅ All prerequisites satisfied")
        return True
    
    def generate_summary_report(self) -> str:
        """Generate a summary report of the pipeline execution."""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        self.results["end_time"] = end_time.isoformat()
        self.results["total_duration_seconds"] = total_duration
        
        # Count successful steps
        successful_steps = sum(1 for step in self.results["steps"] if step["success"])
        total_steps = len(self.results["steps"])
        
        # Determine overall success
        self.results["success"] = (self.results["total_errors"] == 0 and 
                                 successful_steps == total_steps)
        
        # Generate summary
        summary = f"""
📊 PIPELINE EXECUTION SUMMARY
{'='*50}
Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Total Duration: {total_duration/60:.1f} minutes
Overall Status: {'✅ SUCCESS' if self.results['success'] else '❌ FAILED'}

📋 STEP RESULTS:
{'-'*30}"""
        
        for step in self.results["steps"]:
            status = "✅ PASS" if step["success"] else "❌ FAIL"
            duration = step["duration_seconds"]
            summary += f"\n{step['name']}: {status} ({duration:.1f}s)"
            if not step["success"] and step["error"]:
                summary += f"\n   Error: {step['error']}"
        
        summary += f"""

📈 STATISTICS:
{'-'*30}
Total Steps: {total_steps}
Successful Steps: {successful_steps}
Failed Steps: {total_steps - successful_steps}
Total Errors: {self.results['total_errors']}
"""
        
        if self.config.get("email_notifications", False):
            summary += f"\n📧 Email notifications: Enabled"
        
        return summary
    
    def save_results(self):
        """Save detailed results to JSON file."""
        results_dir = Path("logs")
        results_dir.mkdir(exist_ok=True)
        
        results_file = results_dir / f"pipeline_results_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.logger.info(f"📄 Detailed results saved to: {results_file}")
    
    def run_pipeline(self) -> bool:
        """Execute the complete pipeline."""
        try:
            # Check prerequisites
            if not self.check_prerequisites():
                return False
            
            self.logger.info("🚀 Starting automated email processing pipeline")
            
            # Define pipeline steps
            steps = [
                ("Email Ingestion", self.step_email_ingestion),
                ("LLM Extraction", self.step_llm_extraction),
                ("Address Geocoding", self.step_geocoding),
                ("S3 Upload", self.step_s3_upload),
                ("Cleanup & Archiving", self.step_cleanup)
            ]
            
            # Execute each step
            for step_name, step_func in steps:
                if self.config.get("stop_on_error", True) and self.results["total_errors"] > 0:
                    self.logger.warning(f"⏹️  Stopping pipeline due to previous errors")
                    break
                
                success = step_func()
                if not success and self.config.get("stop_on_error", True):
                    self.logger.error(f"⏹️  Pipeline stopped due to failure in {step_name}")
                    break
                
                # Brief pause between steps
                if success:
                    time.sleep(2)
            
            # Generate and log summary
            summary = self.generate_summary_report()
            self.logger.info(summary)
            
            # Save detailed results
            self.save_results()
            
            return self.results["success"]
            
        except Exception as e:
            self.logger.error(f"💥 Pipeline failed with unexpected error: {e}")
            self.results["total_errors"] += 1
            return False


def load_config(config_path: str) -> Dict:
    """Load configuration from JSON file."""
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}


def create_default_config() -> Dict:
    """Create default pipeline configuration."""
    return {
        "max_emails": 50,
        "email_folder": "Intake",
        "no_move_emails": False,
        "extraction_limit": None,
        "resume_extraction": True,
        "archive_after_extraction": True,
        "enable_geocoding": True,
        "geocoding_limit": None,
        "enable_s3_upload": False,
        "s3_upload_limit": None,
        "enable_db_ingestion": False,
        "db_ingestion_limit": None,
        "enable_cleanup": True,
        "stop_on_error": True,
        "email_notifications": False
    }


def save_config_template(config_path: str):
    """Save a configuration template file."""
    config = create_default_config()
    
    # Add comments to the config
    config["_comments"] = {
        "max_emails": "Maximum number of emails to fetch per run",
        "email_folder": "Outlook folder to process (e.g., 'Intake', 'Inbox')",
        "no_move_emails": "Set to true to leave emails in original folder",
        "extraction_limit": "Limit number of emails to extract (null for all)",
        "resume_extraction": "Skip emails already processed",
        "archive_after_extraction": "Move processed emails to archive",
        "enable_geocoding": "Add coordinates to patient addresses",
        "geocoding_limit": "Limit geocoding operations (null for all)",
        "enable_s3_upload": "Upload documents to S3",
        "s3_upload_limit": "Limit S3 uploads (null for all)",
        "enable_db_ingestion": "Ingest extracted data into database",
        "db_ingestion_limit": "Limit database ingestion (null for all)",
        "enable_cleanup": "Archive processed email directories",
        "stop_on_error": "Stop pipeline if any step fails",
        "email_notifications": "Send email notifications (future feature)"
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"📄 Configuration template saved to: {config_path}")
    print("Edit this file to customize pipeline behavior")


def main():
    parser = argparse.ArgumentParser(description="Automated Email Processing Pipeline")
    parser.add_argument("--config", type=str, help="Path to configuration JSON file")
    parser.add_argument("--create-config", type=str, help="Create configuration template file")
    parser.add_argument("--max-emails", type=int, default=50, help="Maximum emails to process")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")
    parser.add_argument("--skip-s3", action="store_true", help="Skip S3 upload step")
    parser.add_argument("--skip-geocoding", action="store_true", help="Skip geocoding step")
    parser.add_argument("--skip-db", action="store_true", help="Skip database ingestion step")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue pipeline even if steps fail")
    
    args = parser.parse_args()
    
    # Handle config template creation
    if args.create_config:
        save_config_template(args.create_config)
        return 0
    
    # Load configuration
    config = create_default_config()
    if args.config:
        file_config = load_config(args.config)
        config.update(file_config)
    
    # Apply command-line overrides
    config["max_emails"] = args.max_emails
    config["enable_s3_upload"] = not args.skip_s3
    config["enable_geocoding"] = not args.skip_geocoding
    config["enable_db_ingestion"] = not args.skip_db
    config["stop_on_error"] = not args.continue_on_error
    
    if args.dry_run:
        print("🔍 DRY RUN - Pipeline configuration:")
        print(json.dumps(config, indent=2))
        print("\n📋 Steps that would be executed:")
        steps = ["Email Ingestion", "LLM Extraction", "Address Geocoding", "S3 Upload", "Cleanup & Archiving"]
        for i, step in enumerate(steps, 1):
            if step == "S3 Upload" and not config["enable_s3_upload"]:
                print(f"  {i}. {step} (SKIPPED)")
            elif step == "Address Geocoding" and not config["enable_geocoding"]:
                print(f"  {i}. {step} (SKIPPED)")
            else:
                print(f"  {i}. {step}")
        return 0
    
    # Run the pipeline
    pipeline = PipelineRunner(config)
    success = pipeline.run_pipeline()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())