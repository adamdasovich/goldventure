# Live Event Streaming Guide

This guide explains how to test and use the live event streaming functionality.

## Overview

The platform now supports live video streaming using third-party streaming services (YouTube Live, Twitch, Vimeo, etc.) via embedded iframe players.

## Quick Start (Tomorrow After YouTube Verification)

Once your YouTube verification is complete, follow these steps:

### 1. Download OBS Studio (2 minutes)
- Go to https://obsproject.com/download
- Download Windows installer (~120MB)
- Run installer with default settings

### 2. Get YouTube Stream Key (3 minutes)
- Go to [YouTube Studio](https://studio.youtube.com)
- Click "Create" → "Go Live"
- Choose "Streaming software"
- Configure:
  - Title: "Test Live Stream - GoldVenture Platform"
  - Privacy: "Unlisted"
  - Category: "Science & Technology"
- Copy your **Stream Key** (keep private!)

### 3. Configure OBS (5 minutes)
- Open OBS Studio
- Settings → Stream
- Service: YouTube
- Paste your Stream Key
- Click OK

### 4. Add Camera Source (2 minutes)
- In OBS main window, Sources panel
- Click "+" → "Video Capture Device"
- Name it "Webcam"
- Select your camera
- Click OK

### 5. Start Streaming (1 minute)
- Click "Start Streaming" in OBS
- Wait 10-20 seconds for stream to start
- Go to YouTube Studio to see your live stream

### 6. Get Embed URL (1 minute)
- In YouTube Studio, click "Share"
- Copy the watch URL (looks like `https://youtube.com/watch?v=VIDEO_ID`)
- Convert to embed format: `https://www.youtube.com/embed/VIDEO_ID`

### 7. Update Event (1 minute)
```bash
cd backend
python manage.py shell
```

```python
from core.models import SpeakerEvent
event = SpeakerEvent.objects.get(id=3)
event.stream_url = 'https://www.youtube.com/embed/YOUR_VIDEO_ID'
event.save()
print(f"Event {event.id} is now streaming!")
```

### 8. View Your Live Stream
- Go to http://localhost:3000/companies/2/events/3
- You should see your live camera feed!
- Test reactions and Q&A features

**Total Setup Time: ~15 minutes**

---

## Setup Instructions

### Option 1: YouTube Live (Recommended for Testing)

1. **Start Streaming to YouTube**
   - Open [YouTube Studio](https://studio.youtube.com)
   - Click "Create" → "Go Live"
   - Choose "Streaming software" (for OBS) or "Webcam" (for quick test)
   - Get your **Stream Key** and **Stream URL**

2. **For OBS Studio Users:**
   - Download [OBS Studio](https://obsproject.com/) (free)
   - Settings → Stream
   - Service: YouTube
   - Paste your Stream Key
   - Click "Start Streaming"

3. **Get the Embed URL:**
   - Once live, go to your YouTube live video page
   - The URL will look like: `https://youtube.com/watch?v=VIDEO_ID`
   - Convert to embed URL: `https://www.youtube.com/embed/VIDEO_ID`
   - Or use YouTube Studio → Share → Embed code

### Option 2: Twitch

1. Go to [Twitch Dashboard](https://dashboard.twitch.tv/)
2. Get your Stream Key
3. Stream using OBS or Streamlabs
4. Get embed URL: `https://player.twitch.tv/?channel=YOUR_CHANNEL&parent=localhost`

### Option 3: Vimeo Live

1. Create a Vimeo Live event
2. Get the embed code
3. Extract the iframe src URL

## Testing Live Events

### Step 1: Create an Event

1. Go to any company page
2. Click "Create Event" (requires staff permissions)
3. Fill in event details:
   - Title, description, topic
   - Scheduled start/end times
   - Duration
   - Format: **Video**
   - Add speakers
4. Leave `stream_url` empty for now
5. Submit (event will be created with status 'scheduled')

### Step 2: Set Event to Live

Use Django shell to update the event:

```bash
cd backend
python manage.py shell
```

```python
from core.models import SpeakerEvent

# Find your event
event = SpeakerEvent.objects.latest('id')
print(f"Event {event.id}: {event.title}")

# Set it to live with stream URL
event.status = 'live'
event.stream_url = 'https://www.youtube.com/embed/YOUR_VIDEO_ID'
event.save()

print("Event is now LIVE!")
```

### Step 3: View the Live Event

1. Navigate to the event detail page: `/companies/{company_id}/events/{event_id}`
2. You should see:
   - **LIVE NOW** banner with pulsing red dot
   - Embedded video player with your stream
   - Viewer count badge
   - Live reactions section below
   - Q&A section

### Step 4: Test Features

**As a Viewer:**
- ✅ Watch the live video stream
- ✅ Send live reactions (👏 👍 🔥 ❤️)
- ✅ Submit questions
- ✅ Upvote questions
- ✅ See participant count

**As a Speaker/Admin:**
- ✅ Stream video/audio from OBS or webcam
- ✅ Monitor reactions in real-time
- ✅ See incoming questions
- ✅ Answer questions live

## Quick Test with Sample Video

If you don't want to set up OBS, you can test with any existing YouTube video:

```python
# Use any public YouTube video for testing
event.stream_url = 'https://www.youtube.com/embed/jfKfPfyJRdk'  # Sample video
event.status = 'live'
event.save()
```

## Stream URL Formats

### YouTube
```
https://www.youtube.com/embed/VIDEO_ID
https://www.youtube.com/embed/VIDEO_ID?autoplay=1
```

### Twitch
```
https://player.twitch.tv/?channel=CHANNEL_NAME&parent=localhost
https://player.twitch.tv/?video=VIDEO_ID&parent=localhost
```

### Vimeo
```
https://player.vimeo.com/video/VIDEO_ID
```

### Daily.co (if you want to add video conferencing)
```
https://YOUR_DOMAIN.daily.co/ROOM_NAME
```

## Troubleshooting

### Video Player Not Showing

1. **Check event status:** Must be `'live'`
2. **Check stream_url:** Must not be empty
3. **Check URL format:** Must be embed URL, not watch URL
4. **Check browser console:** Look for iframe errors

### Iframe Security Errors

If you see errors like "Refused to display in a frame":
- Make sure you're using the embed URL, not the regular URL
- For Twitch, add `&parent=localhost` parameter
- For production, add your domain to the parent parameter

### Video Not Loading

1. **Test the URL directly:** Open the embed URL in a new tab
2. **Check video privacy:** Video must be public or unlisted
3. **Check CORS settings:** Some platforms require whitelisting

## Production Considerations

### Before Going Live:

1. **Update parent domains:**
   - Twitch: `&parent=yourdomain.com`
   - Add your production domain to allowed parents

2. **Add stream URL to create form:**
   - Add input field in create event form
   - Or create admin panel to manage live events

3. **Add status management UI:**
   - Button to go live
   - Button to end event
   - Auto-update status based on schedule

4. **Consider using a dedicated streaming service:**
   - [Daily.co](https://www.daily.co/) - Video conferencing API
   - [Agora](https://www.agora.io/) - Real-time engagement
   - [Mux](https://www.mux.com/) - Video streaming infrastructure

5. **Add WebRTC for interactive features:**
   - Two-way video for panel discussions
   - Screen sharing
   - Breakout rooms

## Current Workflow

1. **Before Event:**
   - Create event via UI (status='scheduled')
   - Event appears on homepage and company page

2. **Going Live:**
   - Start streaming to YouTube/Twitch
   - Use Django shell to update:
     ```python
     event.status = 'live'
     event.stream_url = 'EMBED_URL'
     event.save()
     ```

3. **During Event:**
   - Users see video player
   - Can send reactions
   - Can ask questions
   - Real-time interaction

4. **After Event:**
   ```python
   event.status = 'ended'
   event.recording_url = 'URL_TO_RECORDING'  # Optional
   event.save()
   ```

## Next Steps (Future Enhancements)

- [ ] Add stream URL field to create event form
- [ ] Add "Go Live" button for staff users
- [ ] Add "End Event" button
- [ ] Auto-detect when stream ends
- [ ] Add chat functionality alongside video
- [ ] Add speaker spotlight view
- [ ] Add screen sharing capability
- [ ] Integrate with WebRTC for fully integrated solution
- [ ] Add recording auto-save to event
- [ ] Add analytics dashboard (watch time, peak viewers, etc.)
