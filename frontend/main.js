import { initLayout } from './layout.js';
import './utils.js';

// Import all modularized scripts so Vite bundles them
import './modules/add_quest.js';
import './modules/all_submissions_modal.js';
import './modules/badge_management.js';
import './modules/badge_modal.js';
import './modules/create_game.js';
import './modules/delete_game_modal.js';
import './modules/edit_sponsors.js';
import './modules/flash_modal.js';
import './modules/forgot_password_modal.js';
import './modules/game_info_modal.js';
import './modules/generated_quest.js';
import './modules/index_management.js';
import './modules/join_custom_game_modal.js';
import './modules/leaderboard_modal.js';
import './modules/loading_modal.js';
import './modules/login_modal.js';
import './modules/manage_quests.js';
import './modules/manage_sponsors.js';
import './modules/modal_common.js';
import './modules/notifications.js';
import './modules/push.js';
import './modules/quest_detail_modal.js';
import './modules/quill_common.js';
import './modules/register_modal.js';
import './modules/reset_password_modal.js';
import './modules/shout_board_modal.js';
import './modules/submission_detail_modal.js';
import './modules/submit_photo.js';
import './modules/user_management.js';
import './modules/user_profile_modal.js';

document.addEventListener('DOMContentLoaded', () => {
  initLayout();
});
