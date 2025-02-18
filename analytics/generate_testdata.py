#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import uuid
import hashlib
from datetime import datetime
from fake_useragent import UserAgent
import ipaddress
from src import analytics
from src import config

def generate_random_ip():
    """Generate a random valid IP address (both IPv4 and IPv6)"""
    if random.choice([True, False]):  # 50% chance for IPv4 or IPv6
        # Generate IPv4
        ip = ipaddress.IPv4Address(random.randint(0, 2**32-1))
        # Avoid private and reserved ranges
        while ip.is_private or ip.is_reserved or ip.is_multicast:
            ip = ipaddress.IPv4Address(random.randint(0, 2**32-1))
    else:
        # Generate IPv6
        ip = ipaddress.IPv6Address(random.randint(0, 2**128-1))
        while ip.is_private or ip.is_reserved or ip.is_multicast:
            ip = ipaddress.IPv6Address(random.randint(0, 2**128-1))
    return str(ip)

def generate_random_sha1():
    """Generate a random SHA1 hash"""
    return hashlib.sha1(str(random.random()).encode()).hexdigest()

def generate_random_language():
    """Generate a random language code"""
    languages = ['en-US', 'de-DE', 'fr-FR', 'es-ES', 'it-IT', 'ja-JP', 'zh-CN', 'ko-KR']
    return random.choice(languages)

def main():
    # Initialize analytics
    if not analytics.start():
        print("Failed to initialize analytics")
        return

    ua = UserAgent()
    sessions = []
    
    # Generate 100 sessions
    print("Generating 100 sessions...")
    for _ in range(100):
        session_id = str(uuid.uuid4())
        sessions.append(session_id)
        
        # Generate session data
        ip = generate_random_ip()
        user_agent = ua.random
        language = generate_random_language()
        
        # Save session
        if not analytics.save_session(session_id, ip, user_agent, language):
            print(f"Failed to save session {session_id}")
            continue
            
    # Generate 200 inputs
    print("Generating 200 inputs...")
    style_count = config.get_style_count()
    if style_count == 0:
        style_count = 5  # fallback if no styles configured
        
    for _ in range(200):
        # Select random session
        session = random.choice(sessions)
        
        # Generate input data
        sha1 = generate_random_sha1()
        cache_path = f"cache/{sha1[:2]}/{sha1[2:4]}/{sha1}.jpg"
        face_detected = random.choice([True, False])
        gender = random.choice([0, 1, 2])  # 0=unknown, 1=male, 2=female
        
        if face_detected:
            min_age = random.randint(1, 80)
            max_age = min_age + random.randint(0, 10)
        else:
            min_age = None
            max_age = None
            
        # Save input details
        if not analytics.save_input_image_details(
            session=session,
            sha1=sha1,
            cache_path_and_filename=cache_path,
            face_detected=face_detected,
            gender=gender,
            min_age=min_age,
            max_age=max_age
        ):
            print(f"Failed to save input details for {sha1}")
            continue
            
        # Generate 1-3 outputs for each input
        for _ in range(random.randint(1, 3)):
            style_num = random.randint(0, style_count-1)
            style_name = config.get_style_name(style_num)
            
            output_filename = f"output/{sha1[:2]}/{sha1[2:4]}/{sha1}_{style_name}.jpg"
            
            # 5% chance of being blocked
            is_blocked = random.random() < 0.05
            block_reason = "NSFW content detected" if is_blocked else None
            
            if not analytics.save_generation_details(
                session=session,
                sha1=sha1,
                style=style_name,
                prompt="generated test data",
                output_filename=output_filename,
                isBlocked=1 if is_blocked else 0,
                block_reason=block_reason
            ):
                print(f"Failed to save generation details for {sha1}")
                continue

    print("Test data generation completed!")
    analytics.stop()

if __name__ == "__main__":
    main()
