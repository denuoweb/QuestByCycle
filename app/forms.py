                                                                      
"""
Module: forms
This module contains WTForms definitions for various forms used throughout the application.
"""

                          
import os

                     
from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.fields import DateField, HiddenField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    URL,
    ValidationError,
)

                           
from app.models.badge import Badge

                                                                               
                      
                                                                               
class CSRFProtectForm(FlaskForm):
    """Form used solely for CSRF protection."""
                                                                                                   
    csrf_token = HiddenField()


                                                                               
                                     
                                                                               
class RegistrationForm(FlaskForm):
    """User registration form."""
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()], render_kw={"autocomplete": "new-password"})
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo(
                "password",
                message="Passwords must match."
            )
        ],
        render_kw={"autocomplete": "new-password"},
    )
    accept_license = BooleanField("I agree to the ", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_accept_license(self, field):                               
        """Ensure the user agrees to the terms."""
        if not field.data:
            raise ValidationError(
                "You must agree to the terms of service, license agreement, and privacy policy to register."
            )

class MastodonLoginForm(FlaskForm):
    """Form for logging in via Mastodon OAuth."""
    instance = StringField("Mastodon Instance Domain", validators=[DataRequired()])
    accept_license = BooleanField("I agree to the ", validators=[DataRequired()])
    submit = SubmitField("Login with Mastodon")

    def validate_accept_license(self, field):
        """Ensure the user agrees to the terms when logging in."""
        if not field.data:
            raise ValidationError(
                "You must agree to the terms of service, license agreement, and privacy policy to log in."
            )

class LoginForm(FlaskForm):
    """User login form."""
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
        render_kw={"autocomplete": "current-password"},
    )
    remember_me = BooleanField("Remember Me", default=True)
    submit = SubmitField("Sign In")


class LogoutForm(FlaskForm):
    """User logout form."""
    submit = SubmitField("Logout")


class ForgotPasswordForm(FlaskForm):
    """Forgot password form."""
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")


class UpdatePasswordForm(FlaskForm):
    """Update password form."""
    current_password = PasswordField(
        "Current Password",
        validators=[DataRequired()],
        render_kw={"autocomplete": "current-password"},
    )
    new_password = PasswordField(
        "New Password",
        validators=[DataRequired(), Length(min=8)],
        render_kw={"autocomplete": "new-password"},
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password")],
        render_kw={"autocomplete": "new-password"},
    )
    submit = SubmitField("Update Password")


class ResetPasswordForm(FlaskForm):
    """Reset password form."""
    password = PasswordField(
        "New Password",
        validators=[DataRequired()],
        render_kw={"autocomplete": "new-password"},
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")],
        render_kw={"autocomplete": "new-password"},
    )
    submit = SubmitField("Reset Password")


class AddUserForm(FlaskForm):
    """Add a new user (admin functionality)."""
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
        render_kw={"autocomplete": "new-password"},
    )
    submit = SubmitField("Add User")


class DeleteUserForm(FlaskForm):
    """Delete user account form."""
    submit = SubmitField("Delete Account")


                                                                               
                      
                                                                               
class GameForm(FlaskForm):
    """Form for creating or editing a game."""
    title = StringField("Game Title", validators=[DataRequired()])
    description = StringField(
        "Game Description", validators=[DataRequired(), Length(max=1000)]
    )
    description2 = StringField(
        "Quest Rules", validators=[DataRequired(), Length(max=4500)]
    )
    start_date = DateField("Start Date", format="%Y-%m-%d", validators=[DataRequired()])
    end_date = DateField("End Date", format="%Y-%m-%d", validators=[DataRequired()])
    details = TextAreaField("Game Details")
    awards = TextAreaField("Awards Details")
    beyond = TextAreaField("Sustainability Details")
    game_goal = IntegerField("Game Goal")
    leaderboard_image = FileField(
        "Leaderboard Background Image (height: 400px; .png only)",
        validators=[FileAllowed(["png"], "Images only!")],
    )
    twitter_username = StringField("Twitter Username")
    twitter_api_key = StringField("Twitter API Key")
    twitter_api_secret = StringField("Twitter API Secret")
    twitter_access_token = StringField("Twitter Access Token")
    twitter_access_token_secret = StringField("Twitter Access Token Secret")
    facebook_app_id = StringField("Facebook App ID")
    facebook_app_secret = StringField("Facebook App Secret")
    facebook_access_token = StringField("Facebook Access Token")
    facebook_page_id = StringField("Facebook Page ID")
    instagram_user_id = StringField("Instagram User ID", validators=[Optional()])
    instagram_access_token = StringField("Instagram Access Token", validators=[Optional()])
    calendar_url = StringField("Calendar URL", validators=[Optional(), URL()])
    custom_game_code = StringField("Custom Game Code", validators=[Optional()])
    is_public = BooleanField("Public Game", default=True)
    allow_joins = BooleanField("Allow Joining", default=True)
    admins = SelectMultipleField("Game Admins", coerce=int)
    social_media_liaison_email = StringField("Social Media Liaison Email",
                                            validators=[Optional(), Email()])
    social_media_email_frequency = SelectField(  
        "Email Frequency",  
        choices=[  
            ("hourly", "Hourly"),
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly")
        ],  
        default="weekly"  
    )
    submit = SubmitField("Create Game")


class QuestForm(FlaskForm):
    """Form for creating or editing a quest."""
    enabled = BooleanField("Enabled", default=True)
    is_sponsored = BooleanField("Is Sponsored", default=False)
    category = StringField("Category", validators=[DataRequired()])
    verification_type_choices = [
        ("qr_code", "QR Code"),
        ("photo", "Photo Upload"),
        ("comment", "Comment"),
        ("photo_comment", "Photo Upload and Comment"),
        ("pause", "Pause"),
    ]
    verification_type = SelectField(
        "Submission Requirements",
        choices=verification_type_choices,
        coerce=str,
        validators=[DataRequired()],
    )
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    tips = TextAreaField("Tips", validators=[Optional()])
    points = IntegerField(
        "Points", validators=[DataRequired(), NumberRange(min=1)], default=1
    )
    completion_limit = IntegerField(
        "Completion Limit", validators=[DataRequired(), NumberRange(min=1)], default=1
    )
    frequency = SelectField(
        "Frequency",
        choices=[("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")],
        validators=[DataRequired()],
    )
    badge_id = SelectField("Badge", coerce=int, choices=[], validators=[Optional()])
    badge_name = StringField("Badge Name", validators=[Optional()])
    badge_description = TextAreaField("Badge Description", validators=[Optional()])
    badge_image_filename = FileField(
        "Badge Image",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only!")],
    )
    default_badge_image = SelectField(
        "Select Default Badge Image", coerce=str, choices=[], default=""
    )
    badge_awarded = IntegerField(
        "Badge Awarded (Required Completions)",
        validators=[Optional(), NumberRange(min=0)],
        default=1,
    )
    game_id = HiddenField("Game ID", validators=[DataRequired()])
    submit = SubmitField("Create Quest")

    def __init__(self, *args, category_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.badge_id.choices = [(0, "None")] + [
            (badge.id, badge.name) for badge in Badge.query.all()
        ]
        badge_image_directory = os.path.join(
            self._get_current_app_root(), "static", "images", "badge_images"
        )
        if not os.path.exists(badge_image_directory):
            os.makedirs(badge_image_directory)
        self.default_badge_image.choices = [("", "None")] + [
            (filename, filename) for filename in os.listdir(badge_image_directory)
        ]

    @staticmethod
    def _get_current_app_root():
        """Helper method to retrieve the current application's root path."""
        return current_app.root_path

    def validate_completion_limit(self, field):                               
        """Ensure completion limit is within valid values."""
        valid_completion_limits = set(range(1, 11))
        if field.data not in valid_completion_limits:
            field.data = 1


class QuestImportForm(FlaskForm):
    """Form for importing quests from a CSV file."""
    csv_file = FileField(
        "CSV File",
        validators=[DataRequired(), FileAllowed(["csv"], "CSV files only!")],
    )
    submit = SubmitField("Import Quests")


                                                                               
                                    
                                                                               
class ProfileForm(FlaskForm):
    """Form for updating a user's profile."""
    display_name = StringField("Player/Team Name", validators=[Optional()])
    profile_picture = FileField(
        "Profile Picture",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png"], "Images only!")],
    )
    age_group = SelectField(
        "Age Group",
        choices=[("teen", "Teen"), ("adult", "Adult"), ("senior", "Senior")],
    )
    interests = StringField("Interests", validators=[Optional()])
    ride_description = StringField(
        "Describe the type of riding you like to do:",
        validators=[Optional(), Length(max=500)],
    )
    upload_to_socials = BooleanField("Upload Activities to Social Media", default=True)
    upload_to_mastodon = BooleanField(
        "Upload Activities to Social Media", default=False
    )
    show_carbon_game = BooleanField("Show Carbon Reduction Game", default=True)
    riding_preferences = SelectMultipleField(
        "Riding Preferences",
        choices=[
            ("new_novice", "New and novice rider"),
            ("elementary_school", "In elementary school or younger"),
            ("middle_school", "In Middle school"),
            ("high_school", "In High school"),
            ("college", "College student"),
            ("families", "Families who ride with their children"),
            ("grandparents", "Grandparents who ride with their grandchildren"),
            ("seasoned", "Seasoned riders who ride all over town for their transportation"),
            ("adaptive", "Adaptive bike users"),
            ("occasional", "Occasional rider"),
            ("ebike", "E-bike rider"),
            ("long_distance", "Long distance rider"),
            ("no_car", "Don’t own a car"),
            ("commute", "Commute by bike"),
            ("seasonal", "Seasonal riders: I don’t like riding in inclement weather"),
            ("environmentally_conscious", "Environmentally Conscious Riders"),
            ("social", "Social Riders"),
            ("fitness_focused", "Fitness-Focused Riders"),
            ("tech_savvy", "Tech-Savvy Riders"),
            ("local_history", "Local History or Culture Enthusiasts"),
            ("advocacy_minded", "Advocacy-Minded Riders"),
            ("bike_collectors", "Bike Collectors or Bike Equipment Geek"),
            ("freakbike", "Freakbike rider/maker"),
        ],
        validators=[Optional()],
    )
    submit = SubmitField("Update Profile")


class BikeForm(FlaskForm):
    """Form for updating bike information."""
    bike_picture = FileField(
        "Upload Your Bicycle Picture",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png"], "Images only!")],
    )
    bike_description = StringField(
        "Bicycle Description", validators=[Optional(), Length(max=500)]
    )
    submit = SubmitField("Update Bike")


class QuestSubmissionForm(FlaskForm):
    """Form for submitting quest evidence."""
    evidence = FileField(
        "Upload Evidence",
        validators=[FileAllowed(["jpg", "jpeg", "png", "mp4", "webm", "mov"], "Images or videos only!")],
    )
    comment = TextAreaField("Comment")
    submit = SubmitField("Submit Quest")


class PhotoForm(FlaskForm):
    """Form for photo uploads."""
    photo = FileField(
        validators=[
            DataRequired(),
            FileAllowed(["jpg", "jpeg", "png", "mp4", "webm", "mov"], "Images or videos only!")
        ]
    )


class ShoutBoardForm(FlaskForm):
    """Form for posting messages on the shout board."""
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=500)])
    game_id = HiddenField("Game ID", validators=[DataRequired()])
    submit = SubmitField("Post")


class BadgeForm(FlaskForm):
    """Form for creating or editing a badge."""
    name = StringField("Name", validators=[DataRequired()])
    description = StringField("Description", validators=[DataRequired()])
    category = SelectField("Category", choices=[], validators=[Optional()])
    image = FileField(
        "Badge Image",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png"], "Images only!")],
    )
    submit = SubmitField("Submit")

    def __init__(self, *args, category_choices=None, **kwargs):
        """
        Initialize the BadgeForm.

        Args:
            category_choices (list): List of valid category choices.
        """
        if category_choices is None:
            category_choices = []
        super().__init__(*args, **kwargs)
        self.category.choices = [("none", "None")] + [
            (choice, choice) for choice in category_choices
        ]


class ContactForm(FlaskForm):
    """Form for a contact message."""
    message = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Send")


class SponsorForm(FlaskForm):
    """Form for sponsor submissions."""
    name = StringField("Name", validators=[DataRequired()])
    website = StringField(
        "Website", validators=[Optional(), URL(message="Invalid URL format")]
    )
    logo = FileField(
        "Upload Logo",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png"], "Images only!")],
    )
    description = TextAreaField("Description", validators=[Optional()])
    tier = SelectField(
        "Tier",
        choices=[("Gold", "Gold"), ("Silver", "Silver"), ("Bronze", "Bronze")],
        validators=[DataRequired()],
    )
    game_id = HiddenField("Game ID", validators=[DataRequired()])
    submit = SubmitField("Submit")