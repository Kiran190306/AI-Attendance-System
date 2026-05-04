package com.attendance.app.ui.attendance;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

import com.attendance.app.R;
import com.attendance.app.api.ApiService;
import com.attendance.app.api.AttendanceRecord;
import com.attendance.app.api.RetrofitClient;
import com.attendance.app.utils.NetworkUtil;
import com.attendance.app.utils.TokenManager;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class AttendanceActivity extends AppCompatActivity {

    private static final long REFRESH_INTERVAL_MS = 5000;

    private RecyclerView recyclerView;
    private ProgressBar progressBar;
    private SwipeRefreshLayout swipeRefreshLayout;
    private TextView errorText;
    private TextView emptyText;
    private AttendanceAdapter adapter;

    private TokenManager tokenManager;
    private ApiService apiService;
    private Handler refreshHandler;
    private final Runnable refreshRunnable = new Runnable() {
        @Override
        public void run() {
            loadAttendance();
            refreshHandler.postDelayed(this, REFRESH_INTERVAL_MS);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_attendance);

        tokenManager = new TokenManager(this);
        apiService = RetrofitClient.getApiService();
        refreshHandler = new Handler(Looper.getMainLooper());

        recyclerView = findViewById(R.id.recycler_view);
        progressBar = findViewById(R.id.progress_bar);
        swipeRefreshLayout = findViewById(R.id.swipe_refresh);
        errorText = findViewById(R.id.error_text);
        emptyText = findViewById(R.id.empty_text);

        recyclerView.setLayoutManager(new LinearLayoutManager(this));
        adapter = new AttendanceAdapter(new ArrayList<>());
        recyclerView.setAdapter(adapter);

        swipeRefreshLayout.setOnRefreshListener(this::loadAttendance);
        loadAttendance();
    }

    @Override
    protected void onResume() {
        super.onResume();
        startAutoRefresh();
    }

    @Override
    protected void onPause() {
        stopAutoRefresh();
        super.onPause();
    }

    private void startAutoRefresh() {
        stopAutoRefresh();
        refreshHandler.postDelayed(refreshRunnable, REFRESH_INTERVAL_MS);
    }

    private void stopAutoRefresh() {
        refreshHandler.removeCallbacks(refreshRunnable);
    }

    private void loadAttendance() {
        clearError();
        showEmpty(false);

        if (!NetworkUtil.isNetworkAvailable(this)) {
            swipeRefreshLayout.setRefreshing(false);
            progressBar.setVisibility(View.GONE);
            showError(getString(R.string.error_no_connection));
            showToast(getString(R.string.error_no_connection));
            return;
        }

        progressBar.setVisibility(View.VISIBLE);

        String token = tokenManager.getBearerToken();
        apiService.getAttendance(token).enqueue(new Callback<List<AttendanceRecord>>() {
            @Override
            public void onResponse(Call<List<AttendanceRecord>> call, Response<List<AttendanceRecord>> response) {
                progressBar.setVisibility(View.GONE);
                swipeRefreshLayout.setRefreshing(false);

                if (response.isSuccessful() && response.body() != null) {
                    List<AttendanceRecord> data = response.body();
                    adapter.setData(data);
                    showEmpty(data.isEmpty());
                } else {
                    adapter.setData(new ArrayList<>());
                    Log.e("AttendanceActivity", "Attendance response failed code: " + response.code());
                    String message = getString(R.string.error_server);
                    showError(message);
                    showToast(message);
                }
            }

            @Override
            public void onFailure(Call<List<AttendanceRecord>> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                swipeRefreshLayout.setRefreshing(false);
                adapter.setData(new ArrayList<>());
                Log.e("AttendanceActivity", "Attendance request failed", t);
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

    private void showEmpty(boolean show) {
        emptyText.setVisibility(show ? View.VISIBLE : View.GONE);
    }
}
