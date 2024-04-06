# API Documentation

## Overview
This API provides endpoints for managing tasks related to streaming, such as retrieving video files, setting stream keys, scheduling live streams, and managing scheduled tasks.

## Install

    bundle install

## Run the app

    python Server.py

# REST API

The REST API to the example app is described below.

## Get list of VIdeo

### Request

`GET /get/video`

    localhost:5000//get/video

### Response

    "Video name": [
        "bird.mp4",
        "horse.mp4",
        "idle.mp4",
        "ship.mp4"
    ]

    Date: Thu, 24 Feb 2011 12:36:33 GMT
    Status: 204 No Content
    Connection: close


