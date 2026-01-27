# src/evaluation/alerting.py
from typing import List, Dict
import smtplib
from email.mime.text import MIMEText
from datetime import datetime


class QualityAlerter:
    """Alert on quality issues"""

    def __init__(self, recipients: List[str], smtp_config: Dict = None):
        self.recipients = recipients
        self.smtp_config = smtp_config or {}
        self.alert_history = []

    def check_and_alert(self, results: Dict, run_name: str):
        """Check results and send alerts if needed"""
        issues = []

        # Check each metric
        thresholds = {
            'faithfulness': 0.70,
            'answer_relevancy': 0.80,
            'answer_correctness': 0.70
        }

        for metric, threshold in thresholds.items():
            actual = results.get(metric, 0)
            if actual < threshold:
                gap = threshold - actual
                issues.append(
                    f"{metric}: {actual:.3f} (need {threshold:.2f}, gap: {gap:.3f})")

        if issues:
            self.send_alert(
                severity="HIGH",
                run_name=run_name,
                issues=issues,
                results=results
            )

    def send_alert(self, severity: str, run_name: str,
                   issues: List[str], results: Dict):
        """Send alert email"""
        subject = f"[{severity}] DocuMind Quality Alert - {run_name}"

        body = f"""
DocuMind Evaluation Alert
========================

Run: {run_name}
Time: {datetime.now().isoformat()}
Severity: {severity}

Quality Issues Detected:
{chr(10).join('- ' + issue for issue in issues)}

Full Results:
- Faithfulness: {results.get('faithfulness', 0):.3f}
- Answer Relevancy: {results.get('answer_relevancy', 0):.3f}
- Answer Correctness: {results.get('answer_correctness', 0):.3f}

Action Required:
1. Review evaluation dashboard
2. Check recent code changes
3. Analyze failing test cases
4. Update prompts or configuration

Dashboard: http://localhost:8501
        """

        print(f"\n🚨 ALERT SENT")
        print(f"Subject: {subject}")
        print(f"Recipients: {', '.join(self.recipients)}")
        print(body)

        # In production, send actual email:
        # msg = MIMEText(body)
        # msg['Subject'] = subject
        # msg['From'] = self.smtp_config['from']
        # msg['To'] = ', '.join(self.recipients)
        #
        # with smtplib.SMTP(self.smtp_config['server']) as server:
        #     server.send_message(msg)
