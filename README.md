# CS348_Project

This application manages track meet athletes and results, featuring a live leaderboard and secure database operations.

## Live Application
**[View the Live Leaderboard here](https://project-a646e257-f02d-4c06-95d.uc.r.appspot.com)**

## Features
- SQL Injection Protection: Uses parameterized queries for all database interactions.
- Optimized Performance: Implemented B-Tree indexes on `final_time` and `age` for fast reporting.
- Data Integrity: Configured with IMMEDIATE isolation levels and transaction blocks to prevent data corruption.

## AI Disclosure
Which AI tools were used: 
- Gemini (Google AI)
- Claude

What tasks the AI assisted with: 
- Making sure rank logic made sense when implementing automatic rankings 
- Database Seeding: Generating a Python script to populate the database with 20 random athletes and realistic performance times for different event categories.
- Debugging: Troubleshooting keyError issues and ensuring data consistency between tables 

UI Integration: 
- Guidance on how to create a UI 

How it was verified: 
- Every SQL query was manually tested in the SQLite environment to ensure it returned the correct rankings per event.

