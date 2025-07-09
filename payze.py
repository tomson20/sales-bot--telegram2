import requests
import json
import logging
from typing import Dict, Optional

class PayzeClient:
    """
    Custom Payze client for handling payment operations
    """
    
    def __init__(self, api_key: str, merchant_id: str):
        self.api_key = api_key
        self.merchant_id = merchant_id
        self.base_url = "https://payze.io/api/v1"
        
    def create_invoice(self, amount: int, currency: str = "GEL", 
                      callback_url: Optional[str] = None, 
                      description: Optional[str] = None) -> Dict:
        """
        Create a payment invoice
        
        Args:
            amount: Payment amount in cents (e.g., 40000 for 400 GEL)
            currency: Currency code (default: GEL)
            callback_url: Webhook URL for payment status updates
            description: Payment description
            
        Returns:
            Dict containing pay_url and invoice_id
        """
        try:
            # Convert amount to cents if it's in whole units
            if amount < 1000:  # Assuming amounts less than 1000 are in whole units
                amount_cents = amount * 100
            else:
                amount_cents = amount
                
            payload = {
                "method": "card",
                "amount": amount_cents,
                "currency": currency,
                "callback": callback_url,
                "callbackError": callback_url,
                "preauthorize": False,
                "lang": "KA"
            }
            
            if description:
                payload["description"] = description
                
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.post(
                f"{self.base_url}/payment",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "pay_url": data.get("payUrl"),
                    "invoice_id": data.get("id")
                }
            else:
                logging.error(f"Payze API error: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            logging.error(f"Error creating Payze invoice: {e}")
            return {}
    
    def get_payment_status(self, payment_id: str) -> Dict:
        """
        Get payment status
        
        Args:
            payment_id: Payment ID from Payze
            
        Returns:
            Dict containing payment status
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.get(
                f"{self.base_url}/payment/{payment_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Payze API error: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            logging.error(f"Error getting Payze payment status: {e}")
            return {} 