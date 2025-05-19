
# Integrating Facebook with Your Application

This guide provides detailed instructions on integrating Facebook with your application. It covers obtaining the Facebook App ID, App Secret, Access Token, and Page ID, as well as assigning app roles to system users.

## Prerequisites

- A Facebook developer account.
- Access to Facebook Business Manager (if you are managing business assets).
- Administrative access to the Facebook app you are integrating.

## Connect Game to Facebook and Instagram
Create 'app' here to get app id and app secret: https://developers.facebook.com/
Use this to generate the access token: https://developers.facebook.com/tools/explorer/

Permissions required:
pages_show_list
pages_read_engagement
pages_read_user_content
pages_manage_posts
pages_manage_engagement
instagram_basic
instagram_branded_content_ads_brand
instagram_branded_content_brand
instagram_branded_content_creator

## Step 1: Create a Facebook App

1. **Log in to Facebook for Developers**:
   - Navigate to [Facebook for Developers](https://developers.facebook.com/).
   - Log in with your Facebook account.

2. **Create a New App**:
   - Click on **My Apps** in the top-right corner and select **Create App**.
   - Choose the type of app you are creating (e.g., **Manage Business Integrations**).
   - Enter the **Display Name** for your app and your **Contact Email**.
   - Select your **App Purpose** and click **Create App ID**.
   - Complete any security checks if prompted.

3. **Access App Dashboard**:
   - After creating the app, you will be redirected to the app dashboard.
   - Note down your **App ID**. You will need this for API calls.

## Step 2: Obtain the App Secret

1. **Navigate to App Settings**:
   - In the app dashboard, go to **Settings** > **Basic**.

2. **View App Secret**:
   - Under **App Secret**, click **Show** and enter your Facebook password to reveal the secret.
   - Note down the **App Secret**. Keep this secure and do not share it publicly.

## Step 3: Generate an Access Token

To interact with Facebook APIs, you need an access token. Follow these steps to generate one:

1. **Create a System User (if not already created)**:
   - Go to [Facebook Business Manager](https://business.facebook.com/).
   - Navigate to **Business Settings** > **Users** > **System Users**.
   - Click **Add** to create a new system user if one does not already exist.

2. **Assign App Role to System User**:
   - In **Business Settings**, go to **Users** > **System Users**.
   - Select the system user you want to assign a role to.
   - Click **Assign Assets**, select the app, and choose the appropriate role of **Tester**.

3. **Generate Access Token**:
   - In **System User Details**, click **Generate New Token**.
   - Select the app and choose the necessary permissions:
      - instagram_basic
      - instagram_content_publish
      - pages_manage_posts
      - pages_read_engagement
      - pages_read_user_content
      - publish_video
   - Click **Generate Token** and note down the **Access Token**.
s
## Step 4: Obtain Facebook Page ID

If your app needs to interact with a Facebook Page, you will need the Page ID:

1. **Go to the Facebook Page**:
   - Navigate to the Facebook Page you want to integrate with.

2. **View Page ID**:
   - In the browser’s address bar, you will see a URL like `https://www.facebook.com/yourpage/`.
   - The **Page ID** can be found in the Page’s settings under **About** or by using the Facebook Graph API:
     ```bash
     curl -X GET "https://graph.facebook.com/v19.0/{page-name}?access_token={access-token}"
     ```
Access Token Debugger: `https://developers.facebook.com/tools/debug/accesstoken/`