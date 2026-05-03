package com.attendance.app.api;

public class LoginResponse {
    private String access_token;
    private String token_type;
    private UserData user;

    public LoginResponse() {}

    public LoginResponse(String accessToken, String tokenType, UserData user) {
        this.access_token = accessToken;
        this.token_type = tokenType;
        this.user = user;
    }

    public String getAccessToken() {
        return access_token;
    }

    public void setAccessToken(String accessToken) {
        this.access_token = accessToken;
    }

    public String getTokenType() {
        return token_type;
    }

    public void setTokenType(String tokenType) {
        this.token_type = tokenType;
    }

    public UserData getUser() {
        return user;
    }

    public void setUser(UserData user) {
        this.user = user;
    }

    public static class UserData {
        private int id;
        private String username;
        private String email;

        public UserData() {}

        public UserData(int id, String username, String email) {
            this.id = id;
            this.username = username;
            this.email = email;
        }

        public int getId() {
            return id;
        }

        public String getUsername() {
            return username;
        }

        public String getEmail() {
            return email;
        }
    }
}
