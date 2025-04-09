# Backend Work

- Ability to See Tuturoial Game Without Logging In
- Time Zone Handling
- Consolidate CSS from template files into separate CSS and split `main.css` into those files
- In Windows, `.json` is allowed in image upload

# Admin Overhaul

- user_emails() screen shows wrong navbar
- Add Email All Users to Admin Dashboard Game
- Admin can select to auto upload all submissions or admin can select which submission to manually upload
- Im/Ex AdminDB in Web UI
- Super Admin / Admin Ability to Ban Users and IP
- Proper Warnings on Bad Task Import
- Encrypt `config.toml` private values using environment variables and Game model fields
- Add `config.toml [mail]` to game model and convert index button
- Add Custom Tasks using LLM
- Add OpenAI API to game model
- add limits to task/badge generation AI

# Activity Pub Profile

- Edit Submission Ability
- Implement Notification Alert
- Add commenting and likes on submission detail page
- User Notification on Task Completion
- Move New Task Submission in Profile to Top (Reverse Order)
- Put a calendar somewhere on the QbC site for keeping track of events listed in Available Quests.  
  _Note: Tomoko has started a Google calendar that could be embedded into the page._
- On enlargement of a submission picture, use the player's profile name instead of the button for the user profile or make the player's profile name a link to their profile.
- Add Additional Comment When Submitting a Task Item That Uses QR Verification

# Update

- Sponsors link at bottom
- Reorganize formatting of Detailed Quest modal
- Set `photo_comment` verification type to allow for no comment

# Fix

- When a player goes to a business that is participating in the QbC game, they will ask or look for a QR code. Scanning the code takes you into the game and displays:  
  > "UPLOAD A PHOTO TO COMPLETE 'VISIT LOCAL BUSINESSES BY BIKE AND FIND A QR CODE AT THEIR SHOP TO SHOW YOU WERE THERE'"
  
  Please change the message slightly to say:
  
  > "UPLOAD A PHOTO TO COMPLETE THE QUEST: 'VISIT LOCAL BUSINESSES BY BIKE AND FIND A QR CODE AT THEIR SHOP TO SHOW YOU WERE THERE'"
  
- On the screen for creating or editing a game, please increase the number of characters for the Quest Instructions editable area to 4500 characters.
- Modify Quill for Task Detail and Game Instruction modal, and recent activity 
- Delete Button on shout board not working.
- After Validating a Task, the Total Posts Variable Doesn't Change on the Task List
- Get loading modal working for task submissions
- Register and login emails are not validated dynamically
- add mastodon selection modal and add terms and privacy requirement
