package com.attendance.app;

import android.annotation.SuppressLint;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import com.attendance.app.utils.NetworkUtil;
import com.google.android.material.button.MaterialButton;

public class MainActivity extends AppCompatActivity {
    private static final String APP_URL = "https://ai-attendance-system-vi47.onrender.com";

    private WebView webView;
    private ProgressBar progressBar;
    private View errorContainer;
    private TextView errorText;
    private MaterialButton retryButton;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        progressBar = findViewById(R.id.progressBar);
        webView = findViewById(R.id.webView);
        errorContainer = findViewById(R.id.error_container);
        errorText = findViewById(R.id.error_text);
        retryButton = findViewById(R.id.retry_button);

        retryButton.setOnClickListener(v -> loadPage());

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                showLoading(true);
                hideError();
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                showLoading(false);
            }

            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                Log.e("MainActivity", "WebView error " + errorCode + ": " + description + " for " + failingUrl);
                showWebError(getString(R.string.error_no_connection));
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    Log.e("MainActivity", "WebView request error: " + error.getDescription());
                    showWebError(getString(R.string.error_no_connection));
                }
            }

            @Override
            public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse errorResponse) {
                if (request.isForMainFrame()) {
                    Log.e("MainActivity", "WebView HTTP error: " + errorResponse.getStatusCode());
                    showWebError(getString(R.string.error_server));
                }
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                view.loadUrl(request.getUrl().toString());
                return true;
            }
        });

        loadPage();
    }

    private void loadPage() {
        if (!NetworkUtil.isNetworkAvailable(this)) {
            showWebError(getString(R.string.error_no_connection));
            return;
        }
        hideError();
        webView.loadUrl(APP_URL);
    }

    private void showLoading(boolean show) {
        progressBar.setVisibility(show ? View.VISIBLE : View.GONE);
    }

    private void showWebError(String message) {
        showLoading(false);
        errorText.setText(message);
        errorContainer.setVisibility(View.VISIBLE);
    }

    private void hideError() {
        errorContainer.setVisibility(View.GONE);
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }
}
