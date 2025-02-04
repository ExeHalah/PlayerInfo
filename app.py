from flask import Flask, request, jsonify
import requests
import re
import datetime

app = Flask(__name__)

# ✅ API key validation
def validate_key():
    api_key = request.args.get('key')
    if api_key != 'samirrs':
        return jsonify({"error": "Invalid API key"}), 403
    return None

# ✅ Convert timestamp to readable format
def format_time(timestamp):
    try:
        return datetime.datetime.utcfromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp

# ✅ Fetch character info from external API
def fetch_character_info(skill_id):
    try:
        url = f"https://character-roan.vercel.app/Character_name/Id={skill_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        name_match = re.search(r'"Character Name":\s?"(.*?)"', response.text)
        png_match = re.search(r'"Png Image":\s?"(https://[^"]+\.png)"', response.text)

        if name_match and png_match:
            return name_match.group(1), png_match.group(1)
    except:
        return None, None

# ✅ Convert item IDs into image URLs
def format_item_list(item_list):
    if not item_list:
        return ['Not Found']
    valid_items = [str(item) for item in item_list if 9 <= len(str(item)) <= 11 and str(item).isdigit()]
    return [f"https://www.craftland.freefireinfo.site/output/{item}.png" for item in valid_items] if valid_items else ['Not Found']

# ✅ Format equipped skills
def format_equipped_skills(equipped_skills):
    if not equipped_skills:
        return 'Not Found', []

    formatted_skills = []
    skill_images = []

    for skill in equipped_skills:
        skill_str = str(skill)
        if len(skill_str) > 1 and skill_str[-2] == '0':  # Adjust skill ID if needed
            skill_str = skill_str[:-1] + '6'

        # Fetch character details
        character_name, png_link = fetch_character_info(skill_str)
        if character_name and png_link:
            formatted_skills.append(character_name)
            skill_images.append(png_link)

    return ', '.join(formatted_skills) if formatted_skills else 'Not Found', skill_images

# ✅ Main API route
@app.route('/ExeHalah-PLAYER-INFO')
def fetch_info():
    # Validate API key
    key_validation = validate_key()
    if key_validation:
        return key_validation

    uid = request.args.get('uid')
    region = request.args.get('region')

    if not uid:
        return jsonify({"error": "Please provide UID"}), 400

    # ✅ Valid regions list
    regions = ["ind", "sg", "br", "ru", "id", "tw", "us", "vn", "th", "me", "pk", "cis", "bd", "na"]

    # ✅ If region is provided, validate it
    if region and region.lower() not in regions:
        return jsonify({"error": "Invalid Region. Please enter a valid region."}), 400

    # ✅ Determine regions to search
    search_regions = [region] if region else regions  # Use all regions if none is provided
    player_data = None

    # ✅ Fetch player data by searching through all regions
    for reg in search_regions:
        api_url = f"https://ariiflexlabs-playerinfo.onrender.com/ff_info?uid={uid}&region={reg}"
        try:
            response = requests.get(api_url, timeout=10)
            player_data = response.json()

            # ✅ If player data is found, break the loop
            if "AccountInfo" in player_data and player_data["AccountInfo"].get("AccountName", "Not Found") != "Not Found":
                break
        except:
            pass  # Ignore errors and continue searching in the next region

    # ✅ If no valid player data found, return error
    if not player_data or not player_data.get("AccountInfo") or player_data["AccountInfo"].get("AccountName", "Not Found") == "Not Found":
        return jsonify({"error": "Invalid UID or Region. Please check and try again."}), 400

    # ✅ Fetch wishlist data
    wishlist_url = f"https://ariflex-labs-wishlist-api.vercel.app/items_info?uid={uid}&region={reg}"
    try:
        wishlist_response = requests.get(wishlist_url, timeout=10)
        wishlist_data = wishlist_response.json()
    except requests.RequestException as e:
        app.logger.error(f"Request failed for wishlist: {str(e)}")
    except Exception as e:
        app.logger.error(f"Unexpected error for wishlist: {str(e)}")

    # Extract and format player data
    account_info = player_data.get("AccountInfo", {})
    account_profile_info = player_data.get("AccountProfileInfo", {})
    captain_basic_info = player_data.get("captainBasicInfo", {})
    equipped_skills = account_profile_info.get('EquippedSkills', [])
    formatted_skills, skill_images = format_equipped_skills(equipped_skills)
    guild_info = player_data.get("GuildInfo", {})
    social_info = player_data.get("socialinfo", {})
    pet_info = player_data.get("petInfo", {})
    credit_score = player_data.get("creditScoreInfo", {})
    account_banner_ids = format_item_list([account_info.get('AccountBannerId', 'Not Found')])
    account_avatar_ids = format_item_list([account_info.get('AccountAvatarId', 'Not Found')])
    Title = format_item_list([account_info.get('Title', 'Not Found')])
    pet_id = format_item_list([pet_info.get('id', 'Not Found')])
    skin_id = format_item_list([pet_info.get('skinId', 'Not Found')])
    selected_skill_id = format_item_list([pet_info.get('selectedSkillId', 'Not Found')])
    equipped_outfits = format_item_list(account_profile_info.get('EquippedOutfit', []))
    equipped_weapons = format_item_list(account_info.get('EquippedWeapon', []))
    banner_ids = format_item_list([captain_basic_info.get('bannerId', 'Not Found')])
    head_pics = format_item_list([captain_basic_info.get('headPic', 'Not Found')])
    title = format_item_list([captain_basic_info.get('title', 'Not Found')])
    wishlist_items = wishlist_data.get('items', 'Not Found')

    # Constructing the wishlist part of the response message
    wishlist_details = []
    for item in wishlist_items:
        item_id = item.get('itemId', 'Not Found')
        release_time = format_time(item.get('releaseTime', 'Not Found'))
        
        # Correcting the image field to use the actual function call
        item_image = format_item_list([item.get('itemId', 'Not Found')])

        wishlist_details.append({
            "itemId": item_id,
            "releaseTime": release_time,
            "itemIdImage": item_image[0]  # Since format_item_list returns a list, we can get the first element
        })

    # Construct response message (without credits field)
    player_message_text = {
        "AccountInfo": {
            "AccountBasicInfo": {
                "AccountType": f"{account_info.get('AccountType', 'Not Found')}",
                "AccountName": f"{account_info.get('AccountName', 'Not Found')}",
                "AccountUid": f"{uid}",
                "AccountRegion": f"{account_info.get('AccountRegion', 'Not Found')}",
                "AccountLevel": f"{account_info.get('AccountLevel', 'Not Found')}",
                "AccountEXP": f"{account_info.get('AccountEXP', 'Not Found')}",
                "AccountBannerId": f"{account_info.get('AccountBannerId', 'Not Found')}",
                "AccountAvatarId": f"{account_info.get('AccountAvatarId', 'Not Found')}",
                "AccountBannerIdImage": f"{', '.join(account_banner_ids)}",
                "AccountAvatarIdImage": f"{', '.join(account_avatar_ids)}",
                "BrRankPoint": f"{account_info.get('BrRankPoint', 'Not Found')}",
                "hasElitePass": f"{account_info.get('hasElitePass', 'False')}",
                "Role": f"{account_info.get('Role', 'Not Found')}",
                "AccountBPBadges": f"{account_info.get('AccountBPBadges', 'Not Found')}",
                "AccountBPID": f"{account_info.get('AccountBPID', 'Not Found')}",
                "AccountSeasonId": f"{account_info.get('AccountSeasonId', 'Not Found')}",
                "AccountLikes": f"{account_info.get('AccountLikes', 'Not Found')}",
                "AccountLastLogin": f"{format_time(account_info.get('AccountLastLogin', 'Not Found'))}",
                "CsRankPoint": f"{account_info.get('CsRankPoint', 'Not Found')}",
                "EquippedWeapon": f"{account_info.get('EquippedWeapon', 'Not Found')}",
                "EquippedWeaponImage": f"{', '.join(equipped_weapons)}",
                "BrMaxRank": f"{account_info.get('BrMaxRank', 'Not Found')}",
                "CsMaxRank": f"{account_info.get('CsMaxRank', 'Not Found')}",
                "AccountCreateTime": f"{format_time(account_info.get('AccountCreateTime', 'Not Found'))}",
                "Title": f"{account_info.get('Title', 'Not Found')}",
                "TitleImage": f"{', '.join(Title)}",
                "ReleaseVersion": f"{account_info.get('ReleaseVersion', 'Not Found')}",
                "ShowBrRank": f"{account_info.get('ShowBrRank', 'Not Found')}",
                "ShowCsRank": f"{account_info.get('ShowCsRank', 'Not Found')}"
            },
            "AccountOverview": {
                "EquippedOutfit": f"{account_profile_info.get('EquippedOutfit', 'Not Found')}",
                "EquippedOutfitImage": f"{', '.join(equipped_outfits)}",
                "EquippedSkills": f"{', '.join([name for name in formatted_skills.split(', ') if name])}",
                "EquippedSkillsImage": f"{', '.join(skill_images)}",
            },
            "GuildInfo": {
                "GuildID": f"{guild_info.get('GuildID', 'Not Found')}",
                "GuildName": f"{guild_info.get('GuildName', 'Not Found')}",
                "GuildOwner": f"{guild_info.get('GuildOwner', 'Not Found')}",
                "GuildLevel": f"{guild_info.get('GuildLevel', 'Not Found')}",
                "GuildCapacity": f"{guild_info.get('GuildCapacity', 'Not Found')}",
                "GuildMember": f"{guild_info.get('GuildMember', 'Not Found')}"
            },
            "CaptainBasicInfo": {
                "accountId": f"{captain_basic_info.get('accountId', 'Not Found')}",
                "accountType": f"{captain_basic_info.get('accountType', 'Not Found')}",
                "nickname": f"{captain_basic_info.get('nickname', 'Not Found')}",
                "region": f"{captain_basic_info.get('region', 'Not Found')}",
                "level": f"{captain_basic_info.get('level', 'Not Found')}",
                "exp": f"{captain_basic_info.get('exp', 'Not Found')}",
                "bannerId": f"{captain_basic_info.get('bannerId', 'Not Found')}",
                "headPic": f"{captain_basic_info.get('headPic', 'Not Found')}",
                "bannerIdImage": f"{', '.join(banner_ids)}",
                "headPicImage": f"{', '.join(head_pics)}",
                "lastLoginAt": f"{format_time(captain_basic_info.get('lastLoginAt', 'Not Found'))}",
                "rank": f"{captain_basic_info.get('rank', 'Not Found')}",
                "rankingPoints": f"{captain_basic_info.get('rankingPoints', 'Not Found')}",
                "EquippedWeapon": f"{captain_basic_info.get('EquippedWeapon', 'Not Found')}",
                "EquippedWeaponImage": f"{format_item_list(captain_basic_info.get('EquippedWeapon', 'Not Found'))}",
                "maxRank": f"{captain_basic_info.get('maxRank', 'Not Found')}",
                "csMaxRank": f"{captain_basic_info.get('csMaxRank', 'Not Found')}",
                "createAt": f"{format_time(captain_basic_info.get('createAt', 'Not Found'))}",
                "title": f"{captain_basic_info.get('title', 'Not Found')}",
                "titleImage": f"{', '.join(title)}",
                "releaseVersion": f"{captain_basic_info.get('releaseVersion', 'Not Found')}",
                "showBrRank": f"{captain_basic_info.get('showBrRank', 'Not Found')}",
                "showCsRank": f"{captain_basic_info.get('showCsRank', 'Not Found')}"
            },
            "PetInfo": {
                "id": f"{pet_info.get('id', 'Not Found')}",
                "idImage": f"{', '.join(pet_id)}",
                "name": f"{pet_info.get('name', 'Not Found')}",
                "level": f"{pet_info.get('level', 'Not Found')}",
                "exp": f"{pet_info.get('exp', 'Not Found')}",
                "isSelected": f"{pet_info.get('isSelected', 'Not Found')}",
                "skinId": f"{pet_info.get('skinId', 'Not Found')}",
                "skinIdImage": f"{', '.join(skin_id)}",
                "selectedSkillId": f"{pet_info.get('selectedSkillId', 'Not Found')}",
                "selectedSkillIdImage": f"{', '.join(selected_skill_id)}"
            },
            "SocialInfo": {
                "AccountLanguage": f"{social_info.get('AccountLanguage', 'Not Found')}",
                "AccountSignature": f"{social_info.get('AccountSignature', 'Not Found')}",
                "AccountPreferMode": f"{social_info.get('AccountPreferMode', 'Not Found')}"
            },
            "CreditScoreInfo": {
                "Creditscore": f"{credit_score.get('creditScore', 'Not Found')}",
                "rewardState": f"{credit_score.get('rewardState', '0')}",
                "periodicSummaryStartTime": f"{format_time(credit_score.get('periodicSummaryStartTime', 'Not Found'))}",
                "periodicSummaryEndTime": f"{format_time(credit_score.get('periodicSummaryEndTime', 'Not Found'))}"
            },
            "WishList": wishlist_details,  # Adding wishlist items here
        },
    }

    return jsonify(player_message_text)

if __name__ == '__main__':
    app.config['PROPAGATE_EXCEPTIONS'] = True  # Enable full stack
    app.run(debug=True)
