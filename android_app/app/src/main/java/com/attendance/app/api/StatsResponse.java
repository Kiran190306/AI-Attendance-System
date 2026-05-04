package com.attendance.app.api;

public class StatsResponse {
    private int total_records;
    private int present_today;
    private double avg_confidence;

    public StatsResponse() {}

    public int getTotalRecords() {
        return total_records;
    }

    public void setTotalRecords(int totalRecords) {
        this.total_records = totalRecords;
    }

    public int getPresentToday() {
        return present_today;
    }

    public void setPresentToday(int presentToday) {
        this.present_today = presentToday;
    }

    public double getAvgConfidence() {
        return avg_confidence;
    }

    public void setAvgConfidence(double avgConfidence) {
        this.avg_confidence = avgConfidence;
    }
}
