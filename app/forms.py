from flask_wtf import FlaskForm
from flask import current_app
from wtforms import StringField, SelectField, SubmitField, IntegerField, PasswordField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, NumberRange, EqualTo, Optional, Email, Length, ValidationError, URL
from wtforms.fields import DateField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from app.models import Badge, Task, Game

import os

class CSRFProtectForm(FlaskForm):
    # Used only for CSRF protection
    pass

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    accept_license = BooleanField('I agree to the ', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_accept_license(form, field):
        if not field.data:
            raise ValidationError('You must agree to the terms of service, license agreement, and privacy policy to register.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me', default=True)
    submit = SubmitField('Sign In')


class LogoutForm(FlaskForm):
    submit = SubmitField('Logout')


class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Add User')


class GameForm(FlaskForm):
    title = StringField('Game Title', validators=[DataRequired()])
    description = StringField('Game Description', validators=[DataRequired(), Length(max=1000)])
    description2 = StringField('Task Rules', validators=[DataRequired(), Length(max=1000)])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])  # Use DateField
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])  # Use DateField
    details = TextAreaField('Game Details')
    awards = TextAreaField('Awards Details')
    beyond = TextAreaField('Sustainability Details')
    game_goal = IntegerField('Game Goal')  # Add a default value or make it required
    twitter_username = StringField('Twitter Username')
    twitter_api_key = StringField('Twitter API Key')
    twitter_api_secret = StringField('Twitter API Secret')
    twitter_access_token = StringField('Twitter Access Token')
    twitter_access_token_secret = StringField('Twitter Access Token Secret')
    facebook_app_id = StringField('Facebook App ID')
    facebook_app_secret = StringField('Facebook App Secret')
    facebook_access_token = StringField('Facebook Access Token')
    facebook_page_id = StringField('Facebook Page ID')
    custom_game_code = StringField('Custom Game Code', validators=[Optional()])  # New field for custom game code
    is_public = BooleanField('Public Game', default=True)  # New field for public game indicator
    allow_joins = BooleanField('Allow Joining', default=True)  # New field for allowing new users to join
    submit = SubmitField('Create Game')



class TaskForm(FlaskForm):
    enabled = BooleanField('Enabled', default=True)
    is_sponsored = BooleanField('Is Sponsored', default=False)
    category_choices = [('Environment', 'Environment'), ('Community', 'Community')]  # Example categories
    category = SelectField('Category', choices=category_choices, validators=[DataRequired()])
    verification_type_choices = [
        ('qr_code', 'QR Code'),
        ('photo', 'Photo Upload'),
        ('comment', 'Comment'),
        ('photo_comment', 'Photo Upload and Comment'),
        ('pause', 'Pause')
    ]
    verification_type = SelectField('Submission Requirements', choices=verification_type_choices, coerce=str, validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    tips = TextAreaField('Tips', validators=[Optional()])
    points = IntegerField('Points', validators=[DataRequired(), NumberRange(min=1)], default=1)  # Assuming tasks have at least 1 point
    completion_limit = IntegerField('Completion Limit', validators=[DataRequired(), NumberRange(min=1)], default=1)
    frequency = SelectField('Frequency', choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], validators=[DataRequired()])
    badge_id = SelectField('Badge', coerce=int, choices=[])
    badge_name = StringField('Badge Name', validators=[])
    badge_description = TextAreaField('Badge Description', validators=[])    
    default_badge_image = SelectField('Select Default Badge Image', coerce=str, choices=[], default='')
    badge_image_filename = FileField('Badge Image', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    submit = SubmitField('Create Task')

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.badge_id.choices = [(0, 'None')] + [(badge.id, badge.name) for badge in Badge.query.all()]
        badge_image_directory = os.path.join(current_app.root_path, 'static/images/badge_images')
        if not os.path.exists(badge_image_directory):
            os.makedirs(badge_image_directory)  # Create the directory if it does not exist
        self.default_badge_image.choices = [('','None')] + [(filename, filename) for filename in os.listdir(badge_image_directory)]


class TaskImportForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    tips = TextAreaField('Tips', validators=[])
    points = IntegerField('Points', validators=[DataRequired(), NumberRange(min=1)], default=1)  # Assuming tasks have at least 1 point
    completion_limit = IntegerField('Completion Limit', validators=[DataRequired(), NumberRange(min=1)], default=1)
    frequency = SelectField('Frequency', choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], validators=[DataRequired()])
    verification_type_choices = [
        ('qr_code', 'QR Code'),
        ('photo', 'Photo Upload'),
        ('comment', 'Comment'),
        ('photo_comment', 'Photo Upload and Comment'),
        ('pause', 'Pause')
    ]
    verification_type = SelectField('Submission Requirements', choices=verification_type_choices, coerce=str, validators=[DataRequired()])
    badge_id = SelectField('Select Existing Badge', coerce=int, choices=[], default=0)
    badge_name = StringField('Badge Name', validators=[DataRequired()])
    badge_description = TextAreaField('Badge Description', validators=[DataRequired()])    
    default_badge_image = SelectField('Select Default Badge Image', coerce=str, choices=[], default='')
    badge_image_filename = FileField('Badge Image', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    submit = SubmitField('Add Task')

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.badge_id.choices = [(0, 'None')] + [(b.id, b.name) for b in Badge.query.order_by('name')]
        badge_image_directory = os.path.join(current_app.root_path, 'static/images/badge_images')
        self.default_badge_image.choices = [('','None')] + [(filename, filename) for filename in os.listdir(badge_image_directory)]


class ProfileForm(FlaskForm):
    display_name = StringField('Player/Team Name', validators=[Optional()])
    profile_picture = FileField('Profile Picture', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    age_group = SelectField('Age Group', choices=[('teen', 'Teen'), ('adult', 'Adult'), ('senior', 'Senior')])
    interests = StringField('Interests', validators=[Optional()])
    submit = SubmitField('Update Profile')


class TaskSubmissionForm(FlaskForm):
    evidence = FileField('Upload Evidence', validators=[FileAllowed(['jpg', 'png', 'pdf'], 'Images and PDFs only!')])
    comment = TextAreaField('Comment')  # Assuming you might also want to submit a comment
    submit = SubmitField('Submit Task')


class PhotoForm(FlaskForm):
    photo = FileField(validators=[DataRequired()])
    

class ShoutBoardForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Post')

class BadgeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[])
    image = FileField('Badge Image')
    submit = SubmitField('Submit')

    def __init__(self, category_choices, *args, **kwargs):
        super(BadgeForm, self).__init__(*args, kwargs)
        self.category.choices = [('none', 'None')] + category_choices

class TaskImportForm(FlaskForm):
    csv_file = FileField('CSV File', validators=[DataRequired(), FileAllowed(['csv'], 'CSV files only!')])
    submit = SubmitField('Import Tasks')

class ContactForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')

class SponsorForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    website = StringField('Website', validators=[Optional(), URL()])
    logo = StringField('Logo URL', validators=[Optional(), URL()])
    description = TextAreaField('Description', validators=[Optional()])
    tier = StringField('Tier', validators=[DataRequired()])
    game_id = SelectField('Game', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(SponsorForm, self).__init__(*args, kwargs)
        self.game_id.choices = [(game.id, game.title) for game in Game.query.order_by('title')]

class CarouselImportForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])

class PlayerMessageBoardForm(FlaskForm):
    content = TextAreaField('Message', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Post')