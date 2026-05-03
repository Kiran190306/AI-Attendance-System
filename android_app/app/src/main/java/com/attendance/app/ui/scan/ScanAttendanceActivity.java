package com.attendance.app.ui.scan;

import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.attendance.app.R;
import com.attendance.app.api.ApiService;
import com.attendance.app.api.MarkRequest;
import com.attendance.app.api.MarkResponse;
import com.attendance.app.api.RetrofitClient;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ScanAttendanceActivity extends AppCompatActivity {

    private EditText nameInput;
    private Button scanButton;
    private ProgressBar progressBar;
    private ApiService apiService;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_scan_attendance);

        nameInput = findViewById(R.id.name_input);
        scanButton = findViewById(R.id.scan_button);
        progressBar = findViewById(R.id.progress_bar);

        apiService = RetrofitClient.getApiService();

        scanButton.setOnClickListener(v -> doMark());
    }

    private void doMark() {
        String name = nameInput.getText().toString().trim();
        if (name.isEmpty()) {
            Toast.makeText(this, getString(R.string.error_enter_name), Toast.LENGTH_SHORT).show();
            return;
        }
        progressBar.setVisibility(View.VISIBLE);
        MarkRequest req = new MarkRequest(name, 0.95, "mobile_app");
        apiService.markAttendance(req).enqueue(new Callback<MarkResponse>() {
            @Override
            public void onResponse(Call<MarkResponse> call, Response<MarkResponse> response) {
                progressBar.setVisibility(View.GONE);
                if (response.isSuccessful()) {
                    Toast.makeText(ScanAttendanceActivity.this, getString(R.string.scan_marked), Toast.LENGTH_SHORT).show();
                } else {
                    Toast.makeText(ScanAttendanceActivity.this, getString(R.string.error_server), Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<MarkResponse> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                Log.e("ScanAttendance", "mark failed", t);
                Toast.makeText(ScanAttendanceActivity.this, getString(R.string.error_server), Toast.LENGTH_SHORT).show();
            }
        });
    }
}
