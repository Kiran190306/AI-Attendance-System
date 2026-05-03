package com.attendance.app.api;

public class AttendanceRecord {
    private String student_name;
    private String date;
    private String timestamp;
    private double confidence;

    public AttendanceRecord() {}

    public String getStudentName() {
        return student_name;
    }

    public void setStudentName(String studentName) {
        this.student_name = studentName;
    }

    public String getDate() {
        return date;
    }

    public void setDate(String date) {
        this.date = date;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }

    public double getConfidence() {
        return confidence;
    }

    public void setConfidence(double confidence) {
        this.confidence = confidence;
    }
}
