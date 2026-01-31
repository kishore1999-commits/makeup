# Telugu Bridal Artistry Portfolio

## Overview
A beautiful portfolio website for Supriya.S, a makeup artist specializing in bridal and party makeup. Includes enquiry form with database storage.

## Project Structure
- `index.html` - Main website file (single-page application with embedded CSS and JavaScript)
- `server.py` - Flask backend server with API endpoints and static file serving
- `README.md` - Basic project description

## Technology Stack
- Frontend: HTML/CSS/JavaScript
- Backend: Python Flask
- Database: PostgreSQL (Replit built-in)

## Running the Project
The website runs on port 5000 using Flask:
```bash
python server.py
```

## Deployment
Configured for autoscale deployment using Gunicorn.

## API Endpoints
- `POST /api/enquiry` - Submit new enquiry (name, email, message)
- `GET /api/enquiries` - Get all enquiries as JSON
- `GET /api/enquiries/export` - Export enquiries as CSV (Excel-compatible)

## Database
PostgreSQL database with `enquiries` table:
- id, name, email, message, created_at

## Features
- Responsive design for mobile and desktop
- Image galleries with auto-scroll for bridal, party, and miscellaneous makeup looks
- Modal image viewer with navigation
- Contact/enquiry form with database storage
- Export enquiries to CSV (Excel-compatible)
- Social media links (Instagram, YouTube, Email)
- Testimonials section
