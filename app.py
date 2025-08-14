#!/usr/bin/env python3
"""
Flask Web Interface for YouTube Video Downloader
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import os
import sys
import json
import threading
import time
from pathlib import Path
import tempfile
import uuid
from youtube_downloader import YouTubeDownloader

app = Flask(__name__)
app.secret_key = 'youtube-downloader-secret-key'

# Global storage for download progress
download_progress = {}

class ProgressTracker:
    """Custom progress tracker for web interface"""
    
    def __init__(self, download_id):
        self.download_id = download_id
        self.progress_data = {
            'status': 'starting',
            'percent': 0,
            'speed': '',
            'filename': '',
            'error': None
        }
        download_progress[download_id] = self.progress_data
    
    def progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if d['status'] == 'downloading':
            if 'total_bytes' in d:
                percent = d['downloaded_bytes'] / d['total_bytes'] * 100
                speed = d.get('speed', 0)
                speed_str = f"{speed/1024/1024:.1f} MB/s" if speed else "N/A"
                
                self.progress_data.update({
                    'status': 'downloading',
                    'percent': round(percent, 1),
                    'speed': speed_str,
                    'filename': os.path.basename(d.get('filename', ''))
                })
            elif '_percent_str' in d:
                try:
                    percent_str = d['_percent_str'].strip()
                    percent = float(percent_str.replace('%', ''))
                    self.progress_data.update({
                        'status': 'downloading',
                        'percent': percent,
                        'filename': os.path.basename(d.get('filename', ''))
                    })
                except:
                    pass
                    
        elif d['status'] == 'finished':
            self.progress_data.update({
                'status': 'finished',
                'percent': 100,
                'filename': os.path.basename(d['filename'])
            })

class WebYouTubeDownloader(YouTubeDownloader):
    """Extended YouTube downloader with web progress tracking"""
    
    def __init__(self, download_dir="downloads", progress_tracker=None):
        super().__init__(download_dir)
        self.progress_tracker = progress_tracker
    
    def download_video(self, url, quality='720p', audio_only=False):
        """Download video with web progress tracking"""
        if not self.is_valid_youtube_url(url):
            if self.progress_tracker:
                self.progress_tracker.progress_data['error'] = "Invalid YouTube URL"
            return False
        
        # Get video info first
        video_info = self.get_video_info(url)
        if not video_info:
            if self.progress_tracker:
                self.progress_tracker.progress_data['error'] = "Could not fetch video information"
            return False
        
        # Configure download options
        ydl_opts = {
            'outtmpl': str(self.download_dir / '%(title)s.%(ext)s'),
            'restrictfilenames': True,
        }
        
        if self.progress_tracker:
            ydl_opts['progress_hooks'] = [self.progress_tracker.progress_hook]
        
        if audio_only:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            quality_formats = {
                '720p': 'best[height<=720]',
                '480p': 'best[height<=480]',
                '360p': 'best[height<=360]'
            }
            format_selector = quality_formats.get(quality, 'best[height<=720]')
            ydl_opts['format'] = format_selector
        
        try:
            import yt_dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True
            
        except Exception as e:
            if self.progress_tracker:
                self.progress_tracker.progress_data['error'] = str(e)
            return False

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def start_download():
    """Start a download"""
    data = request.get_json()
    url = data.get('url', '').strip()
    quality = data.get('quality', '720p')
    audio_only = data.get('audio_only', False)
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Generate unique download ID
    download_id = str(uuid.uuid4())
    
    # Create progress tracker
    progress_tracker = ProgressTracker(download_id)
    
    # Start download in background thread
    def download_thread():
        downloader = WebYouTubeDownloader(progress_tracker=progress_tracker)
        try:
            success = downloader.download_video(url, quality, audio_only)
            if not success and not progress_tracker.progress_data.get('error'):
                progress_tracker.progress_data['error'] = "Download failed"
        except Exception as e:
            progress_tracker.progress_data['error'] = str(e)
    
    thread = threading.Thread(target=download_thread)
    thread.daemon = True
    thread.start()
    
    return jsonify({'download_id': download_id})

@app.route('/api/progress/<download_id>')
def get_progress(download_id):
    """Get download progress"""
    progress = download_progress.get(download_id, {
        'status': 'not_found',
        'percent': 0,
        'speed': '',
        'filename': '',
        'error': 'Download not found'
    })
    return jsonify(progress)

@app.route('/api/downloads')
def list_downloads():
    """List downloaded files"""
    download_dir = Path('downloads')
    files = []
    
    if download_dir.exists():
        for file_path in download_dir.glob('*'):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                files.append({
                    'name': file_path.name,
                    'size': f"{size_mb:.1f} MB",
                    'path': str(file_path)
                })
    
    return jsonify({'files': files})

@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    """Get video information"""
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    downloader = YouTubeDownloader()
    if not downloader.is_valid_youtube_url(url):
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    video_info = downloader.get_video_info(url)
    if not video_info:
        return jsonify({'error': 'Could not fetch video information'}), 400
    
    # Format duration
    duration = video_info.get('duration', 0)
    duration_min = duration // 60
    duration_sec = duration % 60
    video_info['duration_formatted'] = f"{duration_min}:{duration_sec:02d}"
    
    return jsonify(video_info)

if __name__ == '__main__':
    # Create downloads directory
    Path('downloads').mkdir(exist_ok=True)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
