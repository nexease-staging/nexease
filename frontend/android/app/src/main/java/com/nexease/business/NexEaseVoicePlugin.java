package com.nexease.business;

import android.Manifest;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.speech.RecognizerIntent;
import androidx.activity.result.ActivityResult;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;
import java.util.ArrayList;

@CapacitorPlugin(name = "NexEaseVoice", permissions = {
    @Permission(alias = "microphone", strings = { Manifest.permission.RECORD_AUDIO })
})
public class NexEaseVoicePlugin extends Plugin {
    @PluginMethod
    public void listen(PluginCall call) {
        if (getPermissionState("microphone") != PermissionState.GRANTED) {
            requestPermissionForAlias("microphone", call, "microphoneResult");
        } else { launchSpeech(call); }
    }

    @PermissionCallback
    private void microphoneResult(PluginCall call) {
        if (getPermissionState("microphone") == PermissionState.GRANTED) { launchSpeech(call); }
        else { call.reject("Microphone permission denied. Enable Microphone in Android Settings > Apps > NexEase > Permissions.", "MICROPHONE_DENIED"); }
    }

    private void launchSpeech(PluginCall call) {
        String language = call.getString("language", "en-IN");
        if (language == null || !language.matches("[a-z]{2,3}(-[A-Za-z]{2,4})?")) { call.reject("Invalid speech language."); return; }
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, language);
        intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1);
        intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak your NexEase command");
        try { startActivityForResult(call, intent, "speechResult"); }
        catch (ActivityNotFoundException exception) { call.reject("No speech service is installed. Enable Google speech recognition or use keyboard dictation.", "SPEECH_UNAVAILABLE"); }
    }

    @ActivityCallback
    private void speechResult(PluginCall call, ActivityResult result) {
        if (call == null) { return; }
        if (result.getResultCode() != Activity.RESULT_OK || result.getData() == null) { call.reject("Voice input cancelled.", "CANCELLED"); return; }
        ArrayList<String> matches = result.getData().getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
        JSObject response = new JSObject();
        response.put("text", matches == null || matches.isEmpty() ? "" : matches.get(0));
        call.resolve(response);
    }
}
