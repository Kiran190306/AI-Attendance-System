package com.attendance.app.utils;

import android.content.Context;
import android.content.SharedPreferences;

public class TokenManager {
    private static final String PREF_NAME = "attendance_token";
    private static final String TOKEN_KEY = "access_token";
    private static final String USER_ID_KEY = "user_id";
    private static final String USERNAME_KEY = "username";

    private SharedPreferences sharedPreferences;

    public TokenManager(Context context) {
        this.sharedPreferences = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
    }

    // Save token
    public void saveToken(String token) {
        sharedPreferences.edit().putString(TOKEN_KEY, token).apply();
    }

    // Get token
    public String getToken() {
        return sharedPreferences.getString(TOKEN_KEY, null);
    }

    // Get token with Bearer prefix
    public String getBearerToken() {
        String token = getToken();
        return token != null ? "Bearer " + token : null;
    }

    // Save user info
    public void saveUser(int userId, String username) {
        sharedPreferences.edit()
                .putInt(USER_ID_KEY, userId)
                .putString(USERNAME_KEY, username)
                .apply();
    }

    // Get user ID
    public int getUserId() {
        return sharedPreferences.getInt(USER_ID_KEY, -1);
    }

    // Get username
    public String getUsername() {
        return sharedPreferences.getString(USERNAME_KEY, null);
    }

    // Check if user is logged in
    public boolean isLoggedIn() {
        return getToken() != null;
    }

    // Clear all data
    public void clearAll() {
        sharedPreferences.edit().clear().apply();
    }
}
