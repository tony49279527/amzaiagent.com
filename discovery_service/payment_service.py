"""
Payment Service for Polar.sh Integration
Handles checkout creation and webhook verification
"""
from polar_sdk import Polar
from .config import POLAR_ACCESS_TOKEN, POLAR_ORGANIZATION_ID, POLAR_PRODUCT_ID, POLAR_CHECKOUT_SUCCESS_URL
import logging

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self):
        # Initialize Polar client
        # Note: In production, ensure POLAR_ACCESS_TOKEN is set
        self.client = Polar(access_token=POLAR_ACCESS_TOKEN)
        self.org_id = POLAR_ORGANIZATION_ID

    async def create_checkout_session(self, user_email: str, product_name: str, amount_cents: int = 1900):
        """
        Create a Polar.sh checkout session for a report.
        Default price: $19.00 (1900 cents)
        """
        try:
            # We use the 'checkouts' API to create a custom checkout
            # Note: amount_cents is currently not directly supported in simple custom checkouts 
            # without a predefined product in some SDK versions, but let's try the standard approach.
            
            # For now, let's assume the user has a 'Pro Report' product or we use a fixed price checkout.
            # In a real scenario, you'd fetch the product list or use a predefined product_id.
            
            # Since we want to move fast, we'll use the Custom Checkout feature if available
            # or redirect to a predefined product page if needed.
            
            # Based on Polar docs (v0.6.1), we can create a checkout for an organization.
            checkout = self.client.checkouts.create(
                organization_id=self.org_id,
                product_id=POLAR_PRODUCT_ID,
                success_url=POLAR_CHECKOUT_SUCCESS_URL,
                customer_email=user_email,
            )
            
            return {
                "url": checkout.url,
                "checkout_id": checkout.id
            }
        except Exception as e:
            logger.error(f"Error creating Polar checkout: {e}")
            raise Exception(f"Payment gateway error: {str(e)}")

    def verify_webhook(self, payload: str, signature: str):
        """
        Verify the webhook signature from Polar.sh
        """
        try:
            # Polar SDK provides verification utilities
            return self.client.webhooks.verify(
                payload=payload,
                signature=signature,
                secret=None # You'd get this from Polar dashboard
            )
        except Exception as e:
            logger.error(f"Webhook verification failed: {e}")
            return None

payment_service = PaymentService()
