
# Admin Guide: Creating a New Game

This guide provides detailed instructions for admins on how to create a new game using the provided form fields. As an admin, you have the ability to create, update, and manage games within the platform.

## Prerequisites

- Admin privileges in the application.
- Access to the admin dashboard.

## Creating a New Game

Follow these steps to create a new game:

### Step 1: Access the Create Game Page

1. **Log in to your Admin Account**:
   - Ensure you are logged in with an account that has admin privileges.

2. **Navigate to the Admin Dashboard**:
   - From the main menu, select **Admin Dashboard**.

3. **Select Create Game**:
   - In the Admin Dashboard, click on **Create Game**.

### Step 2: Fill Out the Game Details

You will see a form with the following fields. Fill them out as described:

1. **Game Title**:
   - **Purpose**: The title of the game is a brief, catchy name that identifies the game.
   - **Interaction**: This title will appear in lists, on the game dashboard, and in notifications to users.
   - **Example**: "Summer Fitness Challenge".

2. **Game Description**:
   - **Purpose**: Provides a brief overview of what the game is about.
   - **Interaction**: This description will appear on the game's main page and gives users an idea of what to expect.
   - **Example**: "Join the Summer Fitness Challenge to stay active and win prizes!".

3. **Quest Instructions**:
   - **Purpose**: Offers detailed instructions for quests participants need to complete.
   - **Interaction**: Displayed in the quest section of the game, guiding participants on how to complete their quests.
   - **Example**: "Complete 30 minutes of exercise daily and log your activities."

4. **Start Date**:
   - **Purpose**: Defines when the game starts.
   - **Interaction**: The game will only become active and visible to participants starting from this date.
   - **Example**: "05/06/2024".

5. **End Date**:
   - **Purpose**: Defines when the game ends.
   - **Interaction**: Participants can no longer complete quests or log activities after this date.
   - **Example**: "06/29/2024".

6. **Game Goal**:
   - **Purpose**: Sets the main objective or target for the game.
   - **Interaction**: Helps participants understand the main focus and end-goal of the game.
   - **Example**: "Complete 1000 push-ups".

7. **Game Details**:
   - **Purpose**: Provides additional, detailed information about the game.
   - **Interaction**: Available to participants who want to learn more about the game structure, rules, or background.
   - **Example**: "Participants must log their activities daily to accumulate points."

8. **Awards Information**:
   - **Purpose**: Describes the prizes or awards that participants can win.
   - **Interaction**: Motivates participants by showing what they can achieve through participation.
   - **Example**: "Top 3 participants will receive a fitness tracker."

9. **Beyond the Game**:
   - **Purpose**: Includes any activities or events related to the game that take place beyond the game itself.
   - **Interaction**: Provides additional value and engagement opportunities for participants.
   - **Example**: "Join our weekly webinars on fitness and nutrition."

10. **Is Public**:
    - **Purpose**: Determines if the game is visible to all users or only to invited participants.
    - **Interaction**: Public games are searchable and joinable by any user, while private games require an invitation or a code.
    - **Example**: Check the box to make the game public.

11. **Allow Joining**:
    - **Purpose**: Allows or restricts new participants from joining the game after it has started.
    - **Interaction**: Ensures that only those who join before a certain point can participate, or keeps the game open for new participants throughout its duration.
    - **Example**: Check the box to allow joining.

12. **Custom Game Code**:
    - **Purpose**: Provides a unique code that participants can use to join the game.
    - **Interaction**: Useful for private or exclusive games where you want to control who can join.
    - **Example**: "SUMMER2024".

13. **Calendar URL**:
    - **Purpose**: Optional link to an external calendar for the game.
    - **Interaction**: When provided, participants see a Calendar tab with the embedded calendar.
    - **Example**: `https://calendar.google.com/calendar/embed?src=your_calendar_id&ctz=America/Los_Angeles`.
14. **Calendar Service JSON Path**:
    - **Purpose**: Path to a Google service account JSON file for syncing calendar events.
    - **Interaction**: When set, new events create quests automatically every 15 minutes.
      Only events scheduled within the next two weeks are imported; past events are ignored.
    - **Example**: `/home/user/service.json`.

### Step 3: Social Media Integration

Fill in the social media integration fields if your game will use Twitter and Facebook. These fields help automate posts and updates related to the game, enhancing engagement and visibility. If these fields are left blank. They will not auto upload to the various social media platform. There are no repercusions.

1. **Twitter Username**:
   - **Purpose**: The Twitter handle used to post updates about the game.
   - **Interaction**: Enables automatic tweeting of game updates, scores, and other notifications.
   - **Example**: `@yourtwitterhandle`.

2. **Twitter API Key**:
   - **Purpose**: The API key used to authenticate requests to Twitter.
   - **Interaction**: Necessary for making authorized requests to Twitter's API.
   - **Example**: `your-twitter-api-key`.

3. **Twitter API Secret**:
   - **Purpose**: The API secret key used along with the API key for authentication.
   - **Interaction**: Provides an additional layer of security for Twitter API requests.
   - **Example**: `your-twitter-api-secret`.

4. **Twitter Access Token**:
   - **Purpose**: The token used to access Twitter API on behalf of the user.
   - **Interaction**: Allows the application to post tweets and perform other actions on Twitter.
   - **Example**: `your-twitter-access-token`.

5. **Twitter Access Token Secret**:
   - **Purpose**: The secret token used along with the access token for secure access.
   - **Interaction**: Ensures secure and authenticated communication with Twitter.
   - **Example**: `your-twitter-access-token-secret`.

6. **Facebook App ID**:
   - **Purpose**: The App ID of your Facebook application.
   - **Interaction**: Used to identify your application when making API requests to Facebook.
   - **Example**: `your-facebook-app-id`.

7. **Facebook App Secret**:
   - **Purpose**: The secret key of your Facebook application.
   - **Interaction**: Used along with the App ID to authenticate API requests.
   - **Example**: `your-facebook-app-secret`.

8. **Facebook Access Token**:
   - **Purpose**: The token used to access Facebook API on behalf of the user.
   - **Interaction**: Allows the application to post updates and retrieve data from Facebook.
   - **Example**: `your-facebook-access-token`.

9. **Facebook Page ID**:
   - **Purpose**: The ID of the Facebook page associated with the game.
   - **Interaction**: Enables the application to post updates to the specific Facebook page.
   - **Example**: `your-facebook-page-id`.

### Step 4: Submit the Form

1. **Review the Information**:
   - Ensure all fields are filled out correctly and review the information provided.

2. **Submit the Form**:
   - Click the **Submit** button to create the game.

### Step 5: Confirmation and Management

1. **Confirmation**:
   - You will receive a confirmation message indicating that the game has been created successfully.

2. **Manage the Game**:
   - You can manage the game from the Admin Dashboard, including updating game details, viewing participants, and managing quests.

## Conclusion

By following this guide, you should be able to create new games as an admin. Ensure that all information provided is accurate and that sensitive information such as API keys and tokens is kept secure.

For more detailed instructions or troubleshooting, refer to the official documentation or contact support.
