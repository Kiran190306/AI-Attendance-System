package com.attendance.app.ui.login;

import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.attendance.app.R;
import com.attendance.app.api.ApiService;
import com.attendance.app.api.LoginRequest;
import com.attendance.app.api.LoginResponse;
import com.attendance.app.api.RetrofitClient;
import com.attendance.app.ui.dashboard.DashboardActivity;
import com.attendance.app.utils.NetworkUtil;
import com.attendance.app.utils.TokenManager;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class LoginActivity extends AppCompatActivity {

    private EditText usernameInput;
    private EditText passwordInput;
    private Button loginButton;
    private Button signupButton;
    private ProgressBar progressBar;
    private TextView errorText;

    private TokenManager tokenManager;
    private ApiService apiService;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        tokenManager = new TokenManager(this);
        apiService = RetrofitClient.getApiService();

        if (tokenManager.isLoggedIn()) {
            startActivity(new Intent(this, DashboardActivity.class));
            finish();
            return;
        }

        usernameInput = findViewById(R.id.username_input);
        passwordInput = findViewById(R.id.password_input);
        loginButton = findViewById(R.id.login_button);
        signupButton = findViewById(R.id.signup_button);
        progressBar = findViewById(R.id.progress_bar);
        errorText = findViewById(R.id.error_text);

        loginButton.setOnClickListener(v -> performLogin());
        signupButton.setOnClickListener(v -> performSignup());
    }

    private void performLogin() {
        if (!validateInputs()) return;

        if (!NetworkUtil.isNetworkAvailable(this)) {
            showError(getString(R.string.error_no_connection));
            return;
        }

        clearError();
        showProgress(true);

        String username = usernameInput.getText().toString().trim();
        String password = passwordInput.getText().toString();
        LoginRequest request = new LoginRequest(username, password);

        apiService.login(request).enqueue(new Callback<LoginResponse>() {
            @Override
            public void onResponse(Call<LoginResponse> call, Response<LoginResponse> response) {
                showProgress(false);

                if (response.isSuccessful() && response.body() != null) {
                    LoginResponse loginResponse = response.body();
                    String token = loginResponse.getAccessToken();
                    LoginResponse.UserData user = loginResponse.getUser();

                    tokenManager.saveToken(token);
                    tokenManager.saveUser(user.getId(), user.getUsername());

                    Intent intent = new Intent(LoginActivity.this, DashboardActivity.class);
                    startActivity(intent);
                    finish();
                } else {
                    Log.e("LoginActivity", "Login failed response code: " + response.code());
                    String message = getErrorMessage(response.code(), getString(R.string.error_login_failed));
                    showError(message);
                    showToast(message);
                }
            }

            @Override
            public void onFailure(Call<LoginResponse> call, Throwable t) {
                showProgress(false);
                Log.e("LoginActivity", "Login request failed", t);
                String message = getString(R.string.error_login_failed);
                showError(message);
                showToast(message);
            }
        });
    }

    private void performSignup() {
        if (!validateInputs()) return;

        if (!NetworkUtil.isNetworkAvailable(this)) {
            showError(getString(R.string.error_no_connection));
            return;
        }

        clearError();
        showProgress(true);

        String username = usernameInput.getText().toString().trim();
        String password = passwordInput.getText().toString();
        LoginRequest request = new LoginRequest(username, password);

        apiService.signup(request).enqueue(new Callback<LoginResponse>() {
            @Override
            public void onResponse(Call<LoginResponse> call, Response<LoginResponse> response) {
                showProgress(false);

                if (response.isSuccessful() && response.body() != null) {
                    LoginResponse signupResponse = response.body();
                    String token = signupResponse.getAccessToken();
                    LoginResponse.UserData user = signupResponse.getUser();

                    tokenManager.saveToken(token);
                    tokenManager.saveUser(user.getId(), user.getUsername());

                    Intent intent = new Intent(LoginActivity.this, DashboardActivity.class);
                    startActivity(intent);
                    finish();
                } else {
                    Log.e("LoginActivity", "Signup failed response code: " + response.code());
                    String message = getErrorMessage(response.code(), getString(R.string.error_signup_failed));
                    showError(message);
                    showToast(message);
                }
            }

            @Override
            public void onFailure(Call<LoginResponse> call, Throwable t) {
                showProgress(false);
                Log.e("LoginActivity", "Signup request failed", t);
                String message = getString(R.string.error_signup_failed);
                showError(message);
                showToast(message);
            }
        });
    }

    private boolean validateInputs() {
        String username = usernameInput.getText().toString().trim();
        String password = passwordInput.getText().toString();

        if (TextUtils.isEmpty(username)) {
            showError(getString(R.string.username_hint) + " is required");
            return false;
        }

        if (TextUtils.isEmpty(password)) {
            showError(getString(R.string.password_hint) + " is required");
            return false;
        }

        if (password.length() < 6) {
            showError("Password must be at least 6 characters");
            return false;
        }

        return true;
    }

    private void showToast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }

    private void showProgress(boolean show) {
        progressBar.setVisibility(show ? View.VISIBLE : View.GONE);
        loginButton.setEnabled(!show);
        signupButton.setEnabled(!show);
    }

    private void showError(String message) {
        errorText.setText(message);
        errorText.setVisibility(View.VISIBLE);
    }

    private void clearError() {
        errorText.setVisibility(View.GONE);
    }

    private String getErrorMessage(int statusCode, String fallback) {
        if (statusCode == 401 || statusCode == 403) {
            return getString(R.string.error_unauthorized);
        }
        if (statusCode >= 500) {
            return getString(R.string.error_server);
        }
        return fallback;
    }
}
