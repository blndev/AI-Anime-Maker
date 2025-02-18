#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import uuid
import hashlib
from datetime import datetime, timedelta
from fake_useragent import UserAgent
import ipaddress
from src import analytics
from src import config

def generate_random_ip():
    """Generate a random valid IP address (both IPv4 and IPv6)"""
    # Generate IPv4
    ip = ipaddress.IPv4Address(random.randint(0, 2**32-1))
    # Avoid private and reserved ranges
    while ip.is_private or ip.is_reserved or ip.is_multicast:
        ip = ipaddress.IPv4Address(random.randint(0, 2**32-1))
    return str(ip)

def generate_random_sha1():
    """Generate a random SHA1 hash"""
    return hashlib.sha1(str(random.random()).encode()).hexdigest()

def generate_random_language():
    """Generate a random language code"""
    languages = ['en-US', 'de-DE', 'fr-FR', 'es-ES', 'it-IT', 'ja-JP', 'zh-CN', 'ko-KR']
    return random.choice(languages)

def generate_past_timestamp(max_days_ago=90):
    """Generate a random timestamp from now up to max_days_ago in the past"""
    now = datetime.now()
    random_days = random.uniform(0, max_days_ago)
    random_time = now - timedelta(days=random_days)
    return random_time

def main():
    # Initialize analytics
    if not analytics.start():
        print("Failed to initialize analytics")
        return

    ua = UserAgent()
    sessions = []
    session_times = {}  # Store session creation times
    
    # Generate 100 sessions
    print("Generating 100 sessions...")
    for _ in range(100):
        session_id = str(uuid.uuid4())
        session_time = generate_past_timestamp()
        sessions.append(session_id)
        session_times[session_id] = session_time
        
        # Generate session data
        ip = generate_random_ip()
        user_agent = ua.random
        language = generate_random_language()
        
        # Save session with timestamp
        if not analytics.save_session(session_id, ip, user_agent, language, session_time):
            print(f"Failed to save session {session_id}")
            continue
    
    # Sort sessions by timestamp for chronological processing
    sessions.sort(key=lambda x: session_times[x])
    
    # Create a pool of SHA1s to ensure some are reused
    sha1_pool = [generate_random_sha1() for _ in range(80)]  # 80 unique images
    frequently_used_sha1 = generate_random_sha1()  # This one will be used multiple times
    sha1_pool.extend([frequently_used_sha1] * 20)  # Add it 20 times to ensure frequent use
    
    # Get style configuration
    style_count = config.get_style_count()
    if style_count == 0:
        style_count = 5  # fallback if no styles configured

    print("Generating random uploads and generations for each session...")
    for session in sessions:
        # Generate 0-8 uploads for each session
        num_uploads = random.randint(0, 8)
        print(f"Generating {num_uploads} uploads for session {session}")
        
        for _ in range(num_uploads):
            # Get timestamp a few minutes after session creation
            upload_time = session_times[session] + timedelta(minutes=random.randint(2, 10))
            
            # Select SHA1 from pool instead of generating new one
            sha1 = random.choice(sha1_pool)
            cache_path = f"cache/{sha1[:2]}/{sha1[2:4]}/{sha1}.jpg"
            face_detected = random.choice([True, False])
            gender = random.choice([0, 1, 2])  # 0=unknown, 1=male, 2=female
            
            if face_detected:
                min_age = random.randint(1, 80)
                max_age = min_age + random.randint(0, 10)
            else:
                min_age = None
                max_age = None
                
            # Save input details with timestamp
            if not analytics.save_input_image_details(
                session=session,
                sha1=sha1,
                cache_path_and_filename=cache_path,
                face_detected=face_detected,
                gender=gender,
                min_age=min_age,
                max_age=max_age,
                timestamp=upload_time
            ):
                print(f"Failed to save input details for {sha1}")
                continue
                
            
            # Generate 0-10 outputs for each upload in general, but have up to 30 for a small amount of images
            num_generations = random.randint(0, 10)
            if num_generations>7:
                if random.randint(0, 100)>80:
                    num_generations = random.randint(0, 30)
                
            print(f"  Generating {num_generations} generations for upload {sha1}")
            
            for _ in range(num_generations):
                style_num = random.randint(0, style_count-1)
                style_name = config.get_style_name(style_num)
                
                output_filename = f"output/{sha1[:2]}/{sha1[2:4]}/{sha1}_{style_name}.jpg"
                
                # 5% chance of being blocked
                is_blocked = random.random() < 0.05
                block_reason = "NSFW content detected" if is_blocked else None
                
                # Generate timestamp between a few minutes to 1 hour after upload
                generation_time = upload_time + timedelta(
                    minutes=random.randint(5, 60)
                )
                
                if not analytics.save_generation_details(
                    session=session,
                    sha1=sha1,
                    style=style_name,
                    prompt="generated test data",
                    output_filename=output_filename,
                    isBlocked=1 if is_blocked else 0,
                    block_reason=block_reason,
                    timestamp=generation_time
                ):
                    print(f"Failed to save generation details for {sha1}")
                    continue

    print("Test data generation completed!")
    analytics.stop()

if __name__ == "__main__":
    main()
