# YouTube Video Downloader

## Overview

This is a Python command-line application that allows users to download YouTube videos with various quality options and audio extraction capabilities. The tool leverages the `yt-dlp` library to handle video downloading and provides a user-friendly interface with real-time progress tracking. The application supports multiple YouTube URL formats and includes robust error handling for common download issues.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture
The application follows a simple object-oriented design with a single main class `YouTubeDownloader` that encapsulates all downloading functionality. This monolithic approach is appropriate for a command-line tool of this scope, keeping the codebase simple and maintainable.

### Command-Line Interface
Uses Python's `argparse` module to handle command-line arguments and options. This provides a standard Unix-style interface that users expect from command-line tools.

### File Management
- Creates a dedicated `downloads` directory (configurable) to organize downloaded content
- Uses Python's `pathlib.Path` for cross-platform file path handling
- Implements proper file naming conventions based on video metadata

### Video Processing Pipeline
The application implements a straightforward pipeline:
1. URL validation using regex patterns
2. Video information extraction via yt-dlp
3. Quality selection and format configuration
4. Download execution with progress tracking
5. File organization and cleanup

### Error Handling Strategy
Implements defensive programming with comprehensive error handling for:
- Invalid YouTube URLs
- Network connectivity issues
- Missing dependencies
- File system permissions
- Video availability restrictions

### Progress Tracking
Uses yt-dlp's built-in progress hooks to provide real-time feedback during downloads, enhancing user experience with percentage completion and download speed information.

## External Dependencies

### Primary Dependencies
- **yt-dlp**: Core video downloading library that handles YouTube's complex streaming protocols and format selection
- **Python Standard Library**: argparse, os, sys, pathlib, re, urllib.parse for core functionality

### System Requirements
- Python 3.6+ runtime environment
- Sufficient disk space for video downloads
- Internet connectivity for accessing YouTube content

### Optional Enhancements
The architecture supports easy extension for additional features like:
- FFmpeg integration for advanced audio/video processing
- Database integration for download history tracking
- GUI framework integration for desktop interface
