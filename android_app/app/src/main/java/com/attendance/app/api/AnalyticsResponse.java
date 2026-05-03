package com.attendance.app.api;

public class AnalyticsResponse {
    private int total_students;
    private int present_today;
    private int late_students;
    private double attendance_percentage;
    private int total_records;
    private int weekly_unique_attendees;

    public AnalyticsResponse() {}

    public int getTotalStudents() {
        return total_students;
    }

    public void setTotalStudents(int totalStudents) {
        this.total_students = totalStudents;
    }

    public int getPresentToday() {
        return present_today;
    }

    public void setPresentToday(int presentToday) {
        this.present_today = presentToday;
    }

    public int getLateStudents() {
        return late_students;
    }

    public void setLateStudents(int lateStudents) {
        this.late_students = lateStudents;
    }

    public double getAttendancePercentage() {
        return attendance_percentage;
    }

    public void setAttendancePercentage(double attendancePercentage) {
        this.attendance_percentage = attendancePercentage;
    }

    public int getTotalRecords() {
        return total_records;
    }

    public void setTotalRecords(int totalRecords) {
        this.total_records = totalRecords;
    }

    public int getWeeklyUniqueAttendees() {
        return weekly_unique_attendees;
    }

    public void setWeeklyUniqueAttendees(int weeklyUniqueAttendees) {
        this.weekly_unique_attendees = weeklyUniqueAttendees;
    }
}
