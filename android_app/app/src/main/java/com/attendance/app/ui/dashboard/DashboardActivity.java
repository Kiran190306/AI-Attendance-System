package com.attendance.app.ui.dashboard;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

import com.attendance.app.R;
import com.attendance.app.api.AnalyticsResponse;
import com.attendance.app.api.ApiService;
import com.attendance.app.api.RetrofitClient;
import com.attendance.app.ui.attendance.AttendanceActivity;
import com.attendance.app.ui.login.LoginActivity;
import com.attendance.app.utils.NetworkUtil;
import com.attendance.app.utils.TokenManager;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class DashboardActivity extends AppCompatActivity {

    private TextView usernameText;
    private TextView totalStudentsText;
    private TextView presentTodayText;
    private TextView attendancePercentageText;
    private TextView errorText;
    private Button viewAttendanceButton;
    private Button logoutButton;
    private ProgressBar progressBar;
    private SwipeRefreshLayout swipeRefreshLayout;

    private TokenManager tokenManager;
    private ApiService apiService;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_dashboard);

        tokenManager = new TokenManager(this);
        apiService = RetrofitClient.getApiService();

        if (!tokenManager.isLoggedIn()) {
            startActivity(new Intent(this, LoginActivity.class));
            finish();
            return;
        }

        usernameText = findViewById(R.id.username_text);
        totalStudentsText = findViewById(R.id.total_students_text);
        presentTodayText = findViewById(R.id.present_today_text);
        attendancePercentageText = findViewById(R.id.attendance_percentage_text);
        errorText = findViewById(R.id.error_text);
        viewAttendanceButton = findViewById(R.id.view_attendance_button);
        logoutButton = findViewById(R.id.logout_button);
        progressBar = findViewById(R.id.progress_bar);
        swipeRefreshLayout = findViewById(R.id.swipe_refresh);

        String username = tokenManager.getUsername();
        usernameText.setText(getString(R.string.welcome_label, username));

        viewAttendanceButton.setOnClickListener(v -> {
            Intent intent = new Intent(this, AttendanceActivity.class);
            startActivity(intent);
        });

        logoutButton.setOnClickListener(v -> logout());
        swipeRefreshLayout.setOnRefreshListener(this::loadAnalytics);
        loadAnalytics();
    }

    private void loadAnalytics() {
        clearError();

        if (!NetworkUtil.isNetworkAvailable(this)) {
            swipeRefreshLayout.setRefreshing(false);
            showError(getString(R.string.error_no_connection));
            return;
        }

        progressBar.setVisibility(View.VISIBLE);

        String token = tokenManager.getBearerToken();
        apiService.getAnalytics(token).enqueue(new Callback<AnalyticsResponse>() {
            @Override
            public void onResponse(Call<AnalyticsResponse> call, Response<AnalyticsResponse> response) {
                progressBar.setVisibility(View.GONE);
                swipeRefreshLayout.setRefreshing(false);

                if (response.isSuccessful() && response.body() != null) {
                    AnalyticsResponse analytics = response.body();
                    totalStudentsText.setText(String.valueOf(analytics.getTotalStudents()));
                    presentTodayText.setText(String.valueOf(analytics.getPresentToday()));
                    attendancePercentageText.setText(String.format("%.1f%%", analytics.getAttendancePercentage()));
                } else {
                    Log.e("DashboardActivity", "Analytics response failed code: " + response.code());
                    String message = getString(R.string.error_server);
                    showError(message);
                    showToast(message);
                }
            }

            @Override
            public void onFailure(Call<AnalyticsResponse> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                swipeRefreshLayout.setRefreshing(false);
                Log.e("DashboardActivity", "Analytics request failed", t);
                String message = getString(R.string.error_server);
                showError(message);
                showToast(message);
            }
        });
    }

    private void showError(String message) {
        errorText.setText(message);
        errorText.setVisibility(View.VISIBLE);
    }

    private void showToast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }

    private void clearError() {
        errorText.setVisibility(View.GONE);
    }

    private void logout() {
        tokenManager.clearAll();
        Intent intent = new Intent(this, LoginActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }
}
