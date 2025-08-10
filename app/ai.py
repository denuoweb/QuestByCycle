"""Create quest with AI help related routes."""
import requests
import string
import re
from flask import Blueprint, jsonify, render_template, request, current_app
from flask_login import login_required
from app.forms import QuestForm
from app.utils.file_uploads import save_badge_image
from app.utils import REQUEST_TIMEOUT, sanitize_html
from .models import db, Quest, Badge
from werkzeug.datastructures import MultiDict
from openai import OpenAI
from io import BytesIO
from PIL import Image

ai_bp = Blueprint('ai', __name__, template_folder='templates')

@ai_bp.route('/generate_quest', methods=['POST'])
@login_required
def generate_quest():
    data = request.get_json()
    description = data.get('description', '')
    game_id = data.get('game_id', '')

    quest_details, error_message = generate_quest_details(description)

    if quest_details:
        generated_quest_html = render_template('generated_quest.html', quest=quest_details, game_id=game_id)
        return jsonify({"generated_quest_html": generated_quest_html})


@ai_bp.route('/create_quest', methods=['POST'])
@login_required
def create_quest():
    form = QuestForm()
    form_data = MultiDict(request.form)
    form.process(form_data)

    if form.validate():
        badge_option = form.badge_option.data
        badge_id = None
        if badge_option in ("individual", "both"):
            badge_id = (
                form.badge_id.data
                if form.badge_id.data and form.badge_id.data != '0'
                else None
            )
            ai_badge_filename = sanitize_html(form_data.get('ai_badge_filename', None))

            if not badge_id and form.badge_name.data:
                badge_image_file = ai_badge_filename
                if 'badge_image_filename' in request.files and not ai_badge_filename:
                    badge_image_file = request.files['badge_image_filename']
                    if badge_image_file and badge_image_file.filename != '':
                        badge_image_file = save_badge_image(badge_image_file)
                    else:
                        return jsonify({"success": False, "message": "No badge image selected for upload."}), 400
                elif ai_badge_filename:
                    badge_image_file = ai_badge_filename
                else:
                    return jsonify({"success": False, "message": "No badge image selected for upload."}), 400

                new_badge = Badge(
                    name=sanitize_html(form.badge_name.data),
                    description=sanitize_html(form.badge_description.data),
                    image=badge_image_file
                )
                db.session.add(new_badge)
                db.session.flush()
                badge_id = new_badge.id

        game_id = sanitize_html(form_data.get('game_id'))
        if not game_id:
            return jsonify({"success": False, "message": "Game ID is required."}), 400

        new_quest = Quest(
            title=sanitize_html(form.title.data),
            description=sanitize_html(form.description.data),
            tips=sanitize_html(form.tips.data),
            points=form.points.data,
            game_id=game_id,
            completion_limit=form.completion_limit.data,
            frequency=sanitize_html(form.frequency.data),
            category=sanitize_html(form.category.data),
            verification_type=sanitize_html(form.verification_type.data),
            badge_awarded=form.badge_awarded.data,
            badge_id=badge_id,
            badge_option=badge_option,
        )
        db.session.add(new_quest)
        try:
            db.session.commit()
            return jsonify({"success": True, "message": "Quest created successfully"}), 201
        except Exception:
            db.session.rollback()
            return


@ai_bp.route('/generate_badge_image', methods=['POST'])
@login_required
def generate_badge_image():
    client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
    data = request.get_json()
    badge_description = data.get('badge_description', '')
    if not badge_description:
        return

    sanitized_badge_description = sanitize_html(badge_description)
    badge_prompt = (
        "Remove any textual inscription in the framing or otherwise and create one uber epic, symbolic, and timeless badge for a Bicycle Quest Quest web app that fits this description while keeping the background invisible (transparent): " + sanitized_badge_description
    )
    response = client.images.generate(
        model="dall-e-3",
        prompt=badge_prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )

                                                     
    generated_image_url = response.data[0].url

                                            
    image_response = requests.get(
        generated_image_url,
        timeout=REQUEST_TIMEOUT,
    )
    if image_response.status_code != 200:
        return jsonify({'error': 'Failed to fetch generated image'}), 500

                                                     
    image = Image.open(BytesIO(image_response.content))
    filename = save_badge_image(image)

    return jsonify({'filename': filename})

def too_many_requests(e=None):
    return render_template('429.html'), 429

def generate_quest_details(description):
    client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
    try:
        quest_prompt = generate_quest_prompt(description)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": quest_prompt},
            ]
        )

        quest_text = response.choices[0].message.content.strip()

        relevance_prompt = f"""
        Based on the quest description:
        {quest_text}
        Is this Quest in any small possible way bicycle, bike, cycle, or cycle-related? Meaning the Quest has been accomplished by bicycle? (Answer with True or False)
        """
        relevance_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": relevance_prompt},
            ]
        )

        is_bicycle_related = relevance_response.choices[0].message.content.strip().strip(string.punctuation).lower()

        if is_bicycle_related == "true":
            quest_details = parse_generated_text(quest_text)

            valid_completion_limits = {1, 2, 3, 4, 5}
            if quest_details['Completion Limit'] not in valid_completion_limits:
                quest_details['Completion Limit'] = 1

            return quest_details, None
        
        else:
            return None, "Generated quest is not bicycle-related."

    except Exception as e:
        return None, f"Failed to generate quest due to an error: {str(e)}"

def generate_quest_prompt(description):
    prompt = f"""
    Here are examples of quests and their respective badges, the format needs to remain:

    Complete Quest:

    Category: Student
    Title: Ride your bike to an after school activity
    Description: Hey, it's time to swap four wheels for the ultimate eco-ride! Gear up, pedal on, and let's make a statement while cruising to the after-school scene. Each turn of the wheel scores you major carbon reduction points, so grab your crew, pump up the tunes, and let's hit the streets. Bikes out, vibes up—let's ride! 🚲✨
    Tips: 🚲 Just do it!
    Points (num): 100
    Completion Limit (num): 1
    Frequency: Daily
    Verification Type (choice): Photo_comment
    Badge Name: Activity Accessor
    Badge Description: Earned by those who extend their cycling beyond the classroom to after school activities. This badge applauds your dedication to staying active and environmentally conscious, highlighting the bike's role in supporting a balanced and engaged lifestyle.

    Complete Quest:

    Category: Errands
    Title: Clean clothes using clean energy.
    Description: Go to the laundromat by bike. Or if you have access to a washer, air dry your clothes to save lots on your energy bill and for the environment.
    Tips: Elevate your laundry game and indulge in the freshest scents! Set up a snazzy clothesline outdoors for that unbeatable, fresh-air dry. 🌞✨🚲
    Points (num): 100
    Completion Limit (num): 4
    Frequency: Weekly
    Verification Type (choice): Photo_comment
    Badge Name: Clean Cycle Laundromat
    Badge Description: For incorporating your bicycle into the routine quest of laundry, this badge applauds your innovative use of clean energy for everyday chores. Your commitment to cycling extends into all aspects of life, promoting a holistic approach to eco-friendly living.

    Complete Quest:

    Category: Work
    Title: Ride your bike to work for a week.
    Description: Hey, eco-warrior! Ready to kick your commute up a notch and ride the green wave to work? Strap on that helmet, grab your trusty steed, and let's pedal our way to a cleaner planet! Each week you ditch the gas guzzler for two wheels, you're not just saving time and money, you're racking up those sweet, sweet carbon reduction points. So let's make this a habit, one pedal stroke at a time.
    Tips: Keep on keeping on, all month long...you can repeat this quest each week.
    Points (num): 120
    Completion Limit (num): 1
    Frequency: Weekly
    Verification Type (choice): Photo_comment
    Badge Name: Commuter Champion
    Badge Description: Earned by choosing the bike as your daily commute to work, this badge honors your contribution to reducing traffic congestion and pollution. Your commitment showcases a model for integrating fitness and environmental stewardship into daily life.

    Complete Quest:

    Category: Food
    Title: Need to get something delivered? Use a pedal-powered delivery service.
    Description: For food deliveries, groceries, letters, packages, visit Pedalers Express or Emerald City Pedicab.
    Tips: Utilize the links provided for more services.
    Points (num): 150
    Completion Limit (num): 4
    Frequency: Weekly
    Verification Type (choice): Photo
    Badge Name: Eco Courier Champion
    Badge Description: For choosing pedal-powered delivery services for your delivery needs, this badge honors your commitment to minimizing environmental impact. Your decision supports sustainable logistics and contributes to a greener, more livable urban space.

    Complete Quest:

    Category: Around Town
    Title: Take a pedicab ride
    Description: Two or three people riding together, how fun! Visit Emerald City Pedicab.
    Tips: Enjoy a fun ride with friends.
    Points (num): 100
    Completion Limit (num): 3
    Frequency: Daily
    Verification Type (choice): Photo_comment
    Badge Name: Eco Joy Rider
    Badge Description: Earned the 'Eco Joy Rider' badge by taking a pedicab ride, making a sustainable choice for your journey. Keep cruising carbon-free and leading the way toward a greener future.

    Frequency field is required to only be one of the following: Daily, Weekly, or Monthly.

    Generate a complete new quest based on the description below making the points be reflective of the difficulty of the quest not to exceed 500 or be below 100, the completion limit and frequency reflective of the repeatability, and verification type to be reflective of if a photo or comment is needed or both.'.

    Description: {description}

    Quest:
    """
    return prompt

def parse_generated_text(response_text):
    try:
                                            
        field_patterns = {
            "Category": r"Category: (.*)",
            "Title": r"Title: (.*)",
            "Description": r"Description: (.*)",
            "Tips": r"Tips: (.*)",
            "Points": r"Points \(num\): (\d+)",
            "Completion Limit": r"Completion Limit \(num\): (\d+)",
            "Frequency": r"Frequency: (.*)",
            "Verification Type": r"Verification Type \(choice\): (.*)",
            "Badge Name": r"Badge Name: (.*)",
            "Badge Description": r"Badge Description: (.*)"
        }

        quest_details = {}
        for field, pattern in field_patterns.items():
            match = re.search(pattern, response_text)
            if match:
                quest_details[field] = match.group(1).strip()
            else:
                raise ValueError(f"{field} field is missing or not correctly formatted")

                                                         
        quest_details['Points'] = int(quest_details['Points'])
        quest_details['Completion Limit'] = int(quest_details['Completion Limit'])

                                                                                         
        if quest_details['Frequency'].lower() not in {'daily', 'weekly', 'monthly'}:
            quest_details['Frequency'] = 'Monthly'                        

        return quest_details
    except (IndexError, ValueError) as e:
        raise ValueError(f"Error parsing response: {str(e)}")
