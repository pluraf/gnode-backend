import re
import base64

# Function to check whether a string is in valid jwt token format without decoding it
def is_valid_jwt_token(token):
    jwt_pattern = re.compile(r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$')
    if not jwt_pattern.match(token):
        return False
    
    # Split the token into header, payload, and signature
    header, payload, signature = token.split('.')
    
    # Define a helper function to check if a string is Base64 URL encoded
    def is_base64_url_encoded(s):
        try:
            # Pad the Base64 string if necessary and decode
            s += '=' * (4 - len(s) % 4)  # Add padding if required
            base64.urlsafe_b64decode(s)
            return True
        except (base64.binascii.Error, ValueError):
            return False
    
    # Check if header, payload, and signature are all Base64 URL encoded
    return is_base64_url_encoded(header) and is_base64_url_encoded(payload) and is_base64_url_encoded(signature)
