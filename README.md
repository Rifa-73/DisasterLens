# 🌊 DisasterLens

## Multimodal AI-Powered Disaster Intelligence Platform

> **Turning scattered disaster information into verified, severity-ranked and actionable intelligence.**

DisasterLens is an AI-powered disaster intelligence platform designed to help identify, analyze, verify and prioritize disaster incidents using **Computer Vision, Deep Learning, Generative AI and multimodal inputs**.

The platform combines information from images, videos, text, optional audio and location data to provide a unified view of disaster situations.

For flood-related incidents, DisasterLens uses a custom-trained **U-Net semantic segmentation model** trained on the **FloodNet dataset** to identify flooded regions and estimate flood coverage and severity.

The system can also analyze multiple images, rank affected areas based on severity, process flood videos frame-by-frame, and apply temporal smoothing to obtain more stable video-level severity estimates.

---

# 🚨 Problem Statement

During a disaster, information is generated from multiple sources:

- 📱 Social media reports
- 📞 Emergency calls
- 🛰️ Satellite and drone imagery
- 📰 News and official alerts
- 📷 User-uploaded images
- 🎥 Disaster videos
- 🎙️ Audio/voice reports
- 📍 Location information

However, this information is often:

- Scattered across different platforms
- Unstructured and difficult to process
- Repetitive or duplicated
- Unverified
- Available in different formats
- Too large for humans to analyze quickly

At the same time, emergency response teams need to answer critical questions:

- Where is the disaster happening?
- How severe is the situation?
- Which areas require immediate attention?
- How much of the area is affected?
- Which incident should be prioritized?
- Is the reported information supported by visual evidence?

### The core challenge

> **Too much information. Too little time.**

DisasterLens addresses this challenge by bringing multiple disaster signals into a unified AI-powered analysis pipeline.

---

# 💡 Our Solution

DisasterLens converts scattered disaster information into structured and actionable intelligence.

# The platform follows an end-to-end pipeline:

User Disaster Sources
        │
        ├── Images
        ├── Videos
        ├── Text
        ├── Audio
        └── Location
        │
        ▼
┌───────────────────────────────┐
│     Multimodal AI Pipeline    │
└───────────────────────────────┘
        │
        ├── Computer Vision
        │      └── U-Net Segmentation
        │
        ├── Video Analysis
        │      └── Frame-wise Segmentation
        │
        ├── Temporal Analysis
        │      └── Smoothing & Stability
        │
        └── Generative AI
               └── Gemini Assessment
        │
        ▼
┌───────────────────────────────┐
│      Incident Intelligence    │
├───────────────────────────────┤
│ Flood Coverage                │
│ Severity Level                │
│ Affected Classes              │
│ Visual Segmentation           │
│ Priority                      │
│ Location                      │
│ AI Reasoning                  │
└───────────────────────────────┘
        │
        ▼
Dashboard + Map + API + Chatbot

# Key Features

- 🌊 **AI-Powered Flood Detection**  
  Detects flood-affected regions from uploaded images using a custom-trained U-Net segmentation model.

- 🎯 **Pixel-Level Flood Segmentation**  
  Classifies image pixels into categories such as flooded buildings, flooded roads, water, vehicles, vegetation, and other scene elements.

- 📊 **Flood Coverage & Severity Assessment**  
  Calculates the percentage of flood-related area and converts it into a severity level such as Low, Medium, or High.

- 🖼️ **Multiple Image Analysis**  
  Analyzes multiple flood images and calculates flood coverage and severity for each image to help identify highly affected areas.

- 🎥 **Video-Based Flood Analysis**  
  Processes video frames to estimate flood coverage over time and identifies peak and average flood severity.

- 🔄 **Temporal Smoothing**  
  Applies temporal smoothing across video frames to reduce sudden prediction fluctuations and provide more stable severity estimates.

- 🤖 **Gemini AI Assessment**  
  Uses Google Gemini for an additional multimodal assessment of disaster type, severity, priority, and reasoning.

- 📍 **Location-Based Incident Reporting**  
  Associates reported incidents with their geographical location for visualization and response planning.

- 🗺️ **Interactive Disaster Map**  
  Displays reported incidents and their severity on an interactive map using Leaflet and OpenStreetMap.

- 🚨 **Severity-Based Prioritization**  
  Helps prioritize incidents based on their estimated severity so that critical situations can receive attention first.

- 💬 **Natural Language Incident Queries**  
  Allows users to ask questions about reported incidents through a Gemini-powered chatbot.

- 🔌 **API-Based AI Integration**  
  Provides FastAPI endpoints for connecting the Computer Vision, Generative AI, database, and frontend components.

- ⚡ **Real-Time Disaster Intelligence Pipeline**  
  Combines image, video, location, and AI-based analysis into a unified disaster assessment workflow.

  ## How It Works

DisasterLens follows a multimodal AI pipeline that converts raw disaster reports into structured intelligence.

```text
User Report
     │
     ├── Image
     ├── Video
     ├── Text
     ├── Audio
     └── Location
     │
     ▼
┌─────────────────────────────┐
│       AI Analysis Layer     │
└─────────────┬───────────────┘
              │
      ┌───────┴────────┐
      ▼                ▼
Computer Vision     Gemini AI
      │                │
      ▼                ▼
U-Net Segmentation  AI Assessment
      │                │
      ▼                ▼
Flood Coverage     Disaster Analysis
      │                │
      └───────┬────────┘
              ▼
      Severity Assessment
              │
              ▼
       Incident Database
              │
              ▼
      FastAPI Backend
              │
        ┌─────┴─────┐
        ▼           ▼
    Dashboard      Map
        │
        ▼
     Chatbot

    
