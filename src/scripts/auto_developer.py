import sys
import os
import logging
import time
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
import mysql.connector

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.services.deep_learning_manager import DeepLearningManager
from src.database.db_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_developer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoDeveloper:
    """Automated Development Assistant"""
    
    def __init__(self, use_api=True):  # API enabled by default
        self.use_api = use_api
        self.db_manager = DatabaseManager()
        
        # Create cache directory
        self.cache_dir = Path('cache')
        self.cache_dir.mkdir(exist_ok=True)
        
        # Configure requests session with retry mechanism
        session = requests.Session()
        retries = Retry(
            total=10,
            backoff_factor=3,
            status_forcelist=[408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        session.mount('https://', HTTPAdapter(max_retries=retries, pool_connections=100, pool_maxsize=100))
        session.mount('http://', HTTPAdapter(max_retries=retries, pool_connections=100, pool_maxsize=100))
        
        # Set longer timeout
        self.default_timeout = (30, 120)  # (connect timeout, read timeout)
        
        # Initialize API managers for different purposes
        if use_api:
            try:
                # Initialize different API managers sharing the same session
                self.dl_manager = DeepLearningManager('alsay', session=session)  # Project management API
                self.db_dl_manager = DeepLearningManager('al', session=session)  # Database API
                self.ui_dl_manager = DeepLearningManager('say', session=session)  # UI API
                logger.info("Successfully initialized API managers")
            except Exception as e:
                logger.error(f"Failed to initialize API managers: {str(e)}")
                # Use cached backup responses
                self._load_backup_responses()
            
        # Development tasks
        self.tasks = [
            "API Connection Testing",
            "MySQL Question Generation",
            "Database Schema Optimization",
            "UI Design Improvement",
            "Performance Enhancement",
            "New Feature Development"
        ]
        
        # Create necessary directories
        self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        Path('logs').mkdir(exist_ok=True)
        
        # Initialize timing variables
        current_time = time.time()
        self.last_api_test = current_time
        self.last_question_gen = current_time
        self.last_db_opt = current_time
        self.last_ui_imp = current_time
        self.last_perf_enh = current_time
        self.last_feature_add = current_time
        
        # Load backup responses
        self._load_backup_responses()
        
    def _load_backup_responses(self):
        """Load backup responses"""
        backup_file = self.cache_dir / 'backup_responses.json'
        if backup_file.exists():
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    self.backup_responses = json.load(f)
                logger.info("Successfully loaded backup responses")
            except Exception as e:
                logger.error(f"Failed to load backup responses: {str(e)}")
                self.backup_responses = {}
        else:
            self.backup_responses = {}
            
    def _save_backup_response(self, key: str, response: str):
        """Save successful response as backup"""
        try:
            backup_file = self.cache_dir / 'backup_responses.json'
            if backup_file.exists():
                with open(backup_file, 'r', encoding='utf-8') as f:
                    responses = json.load(f)
            else:
                responses = {}
            
            responses[key] = {
                'response': response,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(responses, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Successfully saved backup response: {key}")
        except Exception as e:
            logger.error(f"Failed to save backup response: {str(e)}")
        
    def _api_call_with_cache(self, key: str, api_func, *args, **kwargs):
        """API call with caching"""
        try:
            # Try API call
            response = api_func(*args, **kwargs)
            if response:
                # Save successful response as backup
                self._save_backup_response(key, response)
                return response
                
            # API call failed, try using cache
            if key in self.backup_responses:
                logger.warning(f"Using cached backup response: {key}")
                return self.backup_responses[key]['response']
                
            return None
            
        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            # Try using cache
            if key in self.backup_responses:
                logger.warning(f"Using cached backup response: {key}")
                return self.backup_responses[key]['response']
            return None
            
    def run_development_cycle(self, interval=5):  # 5 second interval
        """Run the automated development cycle"""
        logger.info("Starting intelligent development cycle...")
        
        while True:
            try:
                current_time = time.time()
                
                # Test API connection every 15 minutes
                if current_time - self.last_api_test >= 900:  # 15 * 60 seconds
                    self.test_api_connection()
                    self.last_api_test = current_time
                
                # Generate MySQL questions every 10 minutes
                if current_time - self.last_question_gen >= 600:  # 10 * 60 seconds
                    self.generate_mysql_questions()
                    self.last_question_gen = current_time
                
                # Optimize database every 30 minutes
                if current_time - self.last_db_opt >= 1800:  # 30 * 60 seconds
                    self.optimize_database_schema()
                    self.last_db_opt = current_time
                
                # Improve UI every 20 minutes
                if current_time - self.last_ui_imp >= 1200:  # 20 * 60 seconds
                    self.improve_ui_design()
                    self.last_ui_imp = current_time
                
                # Enhance performance every hour
                if current_time - self.last_perf_enh >= 3600:  # 60 * 60 seconds
                    self.enhance_performance()
                    self.last_perf_enh = current_time
                
                # Add new features every 2 hours
                if current_time - self.last_feature_add >= 7200:  # 120 * 60 seconds
                    self.add_new_features()
                    self.last_feature_add = current_time
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Development cycle interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in development cycle: {str(e)}")
                time.sleep(interval)
                
    def test_api_connection(self):
        """Test API connection"""
        try:
            logger.info("Testing API connection...")
            
            # Test simple API call
            test_prompt = "Hello, this is a test message. Please reply with one sentence."
            response = self._api_call_with_cache(
                'api_test_general',
                self.dl_manager.generate_content,
                test_prompt,
                timeout=30,
                system_prompt="You are a test assistant, please reply briefly."
            )
            
            if not response:
                logger.error("API test failed: Empty response")
                return False
                
            logger.info(f"API test response: {response}")
            
            # Test MySQL-related API call
            test_sql_prompt = "Please describe the basic usage of MySQL SELECT statement in one sentence."
            sql_response = self._api_call_with_cache(
                'api_test_mysql',
                self.db_dl_manager.generate_content,
                test_sql_prompt,
                timeout=30,
                system_prompt="You are a MySQL expert, please reply briefly."
            )
            
            if not sql_response:
                logger.error("MySQL API test failed: Empty response")
                return False
                
            logger.info(f"MySQL API test response: {sql_response}")
            
            # Test UI-related API call
            test_ui_prompt = "Please describe what responsive design is in one sentence."
            ui_response = self._api_call_with_cache(
                'api_test_ui',
                self.ui_dl_manager.generate_content,
                test_ui_prompt,
                timeout=30,
                system_prompt="You are a UI design expert, please reply briefly."
            )
            
            if not ui_response:
                logger.error("UI API test failed: Empty response")
                return False
                
            logger.info(f"UI API test response: {ui_response}")
            
            # Save test results
            test_results = {
                'timestamp': datetime.now().isoformat(),
                'general_test': {
                    'prompt': test_prompt,
                    'response': response
                },
                'mysql_test': {
                    'prompt': test_sql_prompt,
                    'response': sql_response
                },
                'ui_test': {
                    'prompt': test_ui_prompt,
                    'response': ui_response
                }
            }
            
            output_file = self.output_dir / f'api_test_{int(time.time())}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(test_results, f, ensure_ascii=False, indent=2)
                
            logger.info("API test completed and results saved")
            return True
            
        except Exception as e:
            logger.error(f"API test failed: {str(e)}")
            return False
            
    def generate_mysql_questions(self):
        """Generate MySQL practice questions"""
        try:
            prompt = """Please generate a MySQL practice question with the following format:
            {
                "question": "Write the question here",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "A/B/C/D",
                "explanation": "Detailed explanation here",
                "difficulty": "beginner/intermediate/advanced"
            }"""
            
            response = self._api_call_with_cache(
                'generate_question',
                self.db_dl_manager.generate_content,
                prompt,
                timeout=60
            )
            
            if response:
                output_file = self.output_dir / f'question_{int(time.time())}.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(response)
                logger.info(f'Successfully generated question and saved to {output_file}')
                return True
            return False
            
        except Exception as e:
            logger.error(f'Failed to generate question: {str(e)}')
            return False
            
    def optimize_database_schema(self):
        """Optimize database schema"""
        try:
            prompt = """Please analyze the following database schema and suggest optimizations:
            1. Table structure improvements
            2. Index recommendations
            3. Query optimization suggestions
            4. Data type optimizations
            5. Performance enhancement tips"""
            
            response = self._api_call_with_cache(
                'db_optimization',
                self.db_dl_manager.generate_content,
                prompt,
                timeout=60
            )
            
            if response:
                output_file = self.output_dir / f'db_optimization_{int(time.time())}.txt'
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(response)
                logger.info(f'Successfully generated database optimization suggestions and saved to {output_file}')
                return True
            return False
            
        except Exception as e:
            logger.error(f'Failed to generate database optimization suggestions: {str(e)}')
            return False
            
    def improve_ui_design(self):
        """Improve UI design"""
        try:
            prompt = """Please provide UI improvement suggestions focusing on:
            1. User experience enhancement
            2. Visual design optimization
            3. Accessibility improvements
            4. Responsive design considerations
            5. Performance optimization"""
            
            response = self._api_call_with_cache(
                'ui_improvements',
                self.ui_dl_manager.generate_content,
                prompt,
                timeout=30
            )
            
            if response:
                output_file = self.output_dir / f'ui_improvements_{int(time.time())}.txt'
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(response)
                logger.info(f'Successfully generated UI improvement suggestions and saved to {output_file}')
                return True
            return False
            
        except Exception as e:
            logger.error(f'Failed to generate UI improvement suggestions: {str(e)}')
            return False
            
    def enhance_performance(self):
        """Enhance system performance"""
        try:
            prompt = """Please analyze the system performance and provide suggestions for:
            1. Code optimization
            2. Resource utilization
            3. Memory management
            4. Response time improvement
            5. Overall system efficiency"""
            
            response = self._api_call_with_cache(
                'performance_optimization',
                self.dl_manager.generate_content,
                prompt,
                timeout=30
            )
            
            if response:
                output_file = self.output_dir / f'performance_optimization_{int(time.time())}.txt'
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(response)
                logger.info(f'Successfully generated performance optimization suggestions and saved to {output_file}')
                return True
            return False
            
        except Exception as e:
            logger.error(f'Failed to generate performance optimization suggestions: {str(e)}')
            return False
            
    def add_new_features(self):
        """Add new features"""
        try:
            prompt = """Please suggest new features considering:
            1. User needs analysis
            2. Feature details
            3. Implementation approach
            4. Testing plan
            Please provide specific feature descriptions and implementation steps."""
            
            response = self._api_call_with_cache(
                'new_features',
                self.dl_manager.generate_content,
                prompt,
                timeout=60
            )
            
            if response:
                output_file = self.output_dir / 'new_features.txt'
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(response)
                logger.info(f'Successfully generated new feature suggestions and saved to {output_file}')
                return True
            return False
            
        except Exception as e:
            logger.error(f'Failed to generate new feature suggestions: {str(e)}')
            return False
            
    def implement_suggestions(self, suggestion_file: str):
        """Implement improvement suggestions"""
        try:
            with open(suggestion_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            prompt = f"""Please convert the following suggestions into implementation code:

{content}

Please provide complete code implementation and deployment steps."""
            
            implementation = self._api_call_with_cache(
                f'implementation_{Path(suggestion_file).stem}',
                self.dl_manager.generate_content,
                prompt,
                timeout=120
            )
            
            if implementation:
                output_file = self.output_dir / f"implementation_{Path(suggestion_file).stem}.py"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(implementation)
                logger.info(f"Successfully converted suggestions to implementation code: {output_file}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to implement suggestions: {str(e)}")
            return False
            
def main():
    """Main function"""
    try:
        # Initialize the automated developer
        developer = AutoDeveloper(use_api=True)
        
        # Start the development cycle
        logger.info("Starting automated development assistant...")
        developer.run_development_cycle()
        
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Program error: {str(e)}")
        
if __name__ == "__main__":
    main() 