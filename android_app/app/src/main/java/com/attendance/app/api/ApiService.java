package com.attendance.app.api;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.POST;
import retrofit2.http.Header;
import java.util.List;

public interface ApiService {

    @POST("/api/login")
    Call<LoginResponse> login(@Body LoginRequest request);

    @POST("/api/signup")
    Call<LoginResponse> signup(@Body LoginRequest request);

    @GET("/api/stats")
    Call<StatsResponse> getStats(@Header("Authorization") String token);

    @GET("/api/attendance")
    Call<List<AttendanceRecord>> getAttendance(@Header("Authorization") String token);

    @POST("/api/mark_attendance")
    Call<MarkResponse> markAttendance(@Body MarkRequest request);
}
