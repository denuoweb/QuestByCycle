from requests_oauthlib import OAuth1Session
from flask import url_for

from .utils import REQUEST_TIMEOUT

import requests
import json
import mimetypes


def post_to_social_media(image_url, image_path, status, game):
    twitter_url, fb_url, instagram_url = None, None, None

    if (
        game.twitter_api_key
        and game.twitter_api_secret
        and game.twitter_access_token
        and game.twitter_access_token_secret
    ):
        media_id, error = upload_media_to_twitter(
            image_path,
            game.twitter_api_key,
            game.twitter_api_secret,
            game.twitter_access_token,
            game.twitter_access_token_secret,
        )
        if not error:
            twitter_url, error = post_to_twitter(
                status,
                media_id,
                game.twitter_username,
                game.twitter_api_key,
                game.twitter_api_secret,
                game.twitter_access_token,
                game.twitter_access_token_secret,
            )

    if game.facebook_access_token and game.facebook_page_id:
        page_access_token = get_facebook_page_access_token(
            game.facebook_access_token,
            game.facebook_page_id,
        )
        media_response = upload_image_to_facebook(
            game.facebook_page_id,
            image_path,
            page_access_token,
        )
        if media_response and 'id' in media_response:
            image_id = media_response['id']
            fb_url, error = post_to_facebook_with_image(
                game.facebook_page_id,
                status,
                image_id,
                page_access_token,
            )


    if game.instagram_user_id and game.instagram_access_token:
        public_image_url = url_for(
            'static',
            filename=image_url,
            _external=True,
        )
        instagram_url, error = post_to_instagram(
            public_image_url,
            status,
            game.instagram_user_id,
            game.instagram_access_token,
        )

    return twitter_url, fb_url, instagram_url


def authenticate_twitter(api_key, api_secret, access_token, access_token_secret):
    return OAuth1Session(api_key, api_secret, access_token, access_token_secret)


def upload_media_to_twitter(
    file_path,
    api_key,
    api_secret,
    access_token,
    access_token_secret,
):
    twitter = authenticate_twitter(
        api_key,
        api_secret,
        access_token,
        access_token_secret,
    )
    url = "https://upload.twitter.com/1.1/media/upload.json"

    with open(file_path, 'rb') as file:
        files = {'media': file}
        response = twitter.post(url, files=files, timeout=REQUEST_TIMEOUT)

        if response.status_code == 200:
            media_id = response.json().get('media_id_string')
            return media_id, None
        else:
            return None, response.text


def post_to_twitter(
    status,
    media_ids,
    twitter_username,
    api_key,
    api_secret,
    access_token,
    access_token_secret,
):
    url = "https://api.twitter.com/2/tweets"
    payload = {
        "text": status,
        "media": {
            "media_ids": [media_ids]
        }
    }
    twitter = authenticate_twitter(
        api_key,
        api_secret,
        access_token,
        access_token_secret,
    )
    response = twitter.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    if response.status_code == 201:
        tweet_id = response.json().get('data').get('id')
        twitter_url = f"https://twitter.com/{twitter_username}/status/{tweet_id}"
        return twitter_url, None
    else:
        return None, response.text


def get_facebook_page_access_token(user_access_token, page_id):
    url = f'https://graph.facebook.com/v19.0/{page_id}'
    params = {
        'fields': 'access_token',
        'access_token': user_access_token
    }
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()['access_token']


def upload_image_to_facebook(page_id, image_path, access_token):
    """Upload an image to Facebook without publishing it."""
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/jpeg"

    url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
    data = {
        "access_token": access_token,
        "published": "false",
    }

    with open(image_path, "rb") as image_file:
        files = {"file": (image_path, image_file, mime_type)}
        response = requests.post(url, files=files, data=data, timeout=REQUEST_TIMEOUT)

    if response.status_code == 200:
        return response.json()
    return None


def post_to_facebook_with_image(page_id, message, media_object_id, access_token):
    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    payload = {
        'message': message,
        'attached_media': json.dumps([{'media_fbid': media_object_id}]),
        'access_token': access_token
    }
    response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    if response.status_code == 200:
        post_id = response.json().get('id')
        fb_url = f"https://www.facebook.com/{post_id}"
        return fb_url, None
    else:
        return None, response.text


def get_instagram_permalink(media_id, access_token):
    permalink_url = f"https://graph.facebook.com/{media_id}?fields=permalink&access_token={access_token}"
    permalink_response = requests.get(permalink_url, timeout=REQUEST_TIMEOUT)
    permalink_data = permalink_response.json()
    if 'permalink' in permalink_data:
        return permalink_data['permalink'], None
    else:
        raise Exception("Permalink not available yet.")


def post_to_instagram(image_url, caption, user_id, access_token):
                                    
    upload_url = f"https://graph.facebook.com/v20.0/{user_id}/media"
    payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': access_token
    }
    response = requests.post(upload_url, data=payload, timeout=REQUEST_TIMEOUT)
    response_data = response.json()
    if 'id' not in response_data:
        raise Exception("Failed to upload image to Instagram.")

    container_id = response_data['id']

                                         
    publish_url = f"https://graph.facebook.com/v20.0/{user_id}/media_publish"
    publish_payload = {
        'creation_id': container_id,
        'access_token': access_token
    }
    publish_response = requests.post(
        publish_url,
        data=publish_payload,
        timeout=REQUEST_TIMEOUT,
    )
    publish_data = publish_response.json()
    if 'id' not in publish_data:
        raise Exception("Failed to publish image on Instagram.")

    media_id = publish_data['id']

                                              
    permalink, error = get_instagram_permalink(media_id, access_token)
    if error:
        raise Exception(error)

    return permalink, None
