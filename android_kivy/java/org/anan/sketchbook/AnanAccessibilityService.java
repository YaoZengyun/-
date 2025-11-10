package org.anan.sketchbook;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.Intent;
import android.os.Build;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import java.util.List;

public class AnanAccessibilityService extends AccessibilityService {
    private static final String TAG = "AnanA11y";
    private static final String ACTION = "org.anan.sketchbook.ACCESS_SENT_TEXT";

    private CharSequence lastTextQQ = null;
    private CharSequence lastTextWX = null;

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null) return;
        CharSequence pkg = event.getPackageName();
        if (pkg == null) return;
        String pkgName = pkg.toString();

        int type = event.getEventType();
        if (type == AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED || type == AccessibilityEvent.TYPE_VIEW_FOCUSED || type == AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED) {
            // 跟踪输入框当前文本
            CharSequence current = extractFocusedText();
            if (current != null) {
                if ("com.tencent.mobileqq".equals(pkgName)) {
                    lastTextQQ = current;
                } else if ("com.tencent.mm".equals(pkgName)) {
                    lastTextWX = current;
                }
            }
        } else if (type == AccessibilityEvent.TYPE_VIEW_CLICKED) {
            // 发送按钮被点击时触发广播
            CharSequence nodeText = event.getText() != null && !event.getText().isEmpty() ? event.getText().get(0) : null;
            // 兼容不同 ROM/主题的按钮文字，可根据需要扩展匹配
            boolean isSendBtn = false;
            if (nodeText != null) {
                String s = nodeText.toString();
                isSendBtn = "发送".equals(s) || "发送(S)".equals(s) || "Send".equalsIgnoreCase(s);
            }
            if (isSendBtn) {
                if ("com.tencent.mobileqq".equals(pkgName)) {
                    broadcastText(String.valueOf(lastTextQQ), pkgName);
                } else if ("com.tencent.mm".equals(pkgName)) {
                    broadcastText(String.valueOf(lastTextWX), pkgName);
                }
            }
        }
    }

    private CharSequence extractFocusedText() {
        try {
            AccessibilityNodeInfo root = getRootInActiveWindow();
            if (root == null) return null;
            // BFS 查找当前可编辑且已聚焦的输入框
            CharSequence result = findFocusedEditableText(root);
            root.recycle();
            return result;
        } catch (Throwable t) {
            Log.w(TAG, "extractFocusedText error", t);
            return null;
        }
    }

    private CharSequence findFocusedEditableText(AccessibilityNodeInfo node) {
        if (node == null) return null;
        if (node.isEditable() && node.isFocused()) {
            CharSequence txt = node.getText();
            if (txt != null) return txt;
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            CharSequence r = findFocusedEditableText(child);
            if (r != null) {
                if (child != null) child.recycle();
                return r;
            }
            if (child != null) child.recycle();
        }
        return null;
    }

    private void broadcastText(String text, String pkg) {
        try {
            if (text == null) return;
            // 可选：只有在出现触发词时才广播，避免频繁触发
            // if (!text.contains("#生成#")) return;
            Intent intent = new Intent(ACTION);
            intent.putExtra("text", text);
            intent.putExtra("package", pkg);
            sendBroadcast(intent);
            Log.i(TAG, "broadcast text from " + pkg + ": " + text);
        } catch (Throwable t) {
            Log.w(TAG, "broadcast error", t);
        }
    }

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        AccessibilityServiceInfo info = new AccessibilityServiceInfo();
        info.eventTypes = AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED
                | AccessibilityEvent.TYPE_VIEW_FOCUSED
                | AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED
                | AccessibilityEvent.TYPE_VIEW_CLICKED;
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
        info.notificationTimeout = 100;
        info.flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
                | AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;
        // 限定监听包提升性能
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR2) {
            info.packageNames = new String[]{"com.tencent.mobileqq", "com.tencent.mm"};
        }
        setServiceInfo(info);
        Log.i(TAG, "Accessibility service connected");
    }

    @Override
    public void onInterrupt() {
        // no-op
    }
}
