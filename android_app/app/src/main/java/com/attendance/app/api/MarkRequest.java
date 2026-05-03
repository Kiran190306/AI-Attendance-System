package com.attendance.app.api;

public class MarkRequest {
    private String student_name;
    private double confidence;
    private String camera;

    public MarkRequest(String student_name, double confidence, String camera) {
        this.student_name = student_name;
        this.confidence = confidence;
        this.camera = camera;
    }

    public String getStudent_name() { return student_name; }
    public double getConfidence() { return confidence; }
    public String getCamera() { return camera; }
}
