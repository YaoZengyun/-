package org.anan.sketchbook;

import android.accessibilityservice.AccessibilityService;
import android.content.Intent;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

public class MyAccService extends AccessibilityService {
    private String lastText = "";
    private static final String ACTION_SENT = "org.anan.sketchbook.ACCESS_SENT_TEXT";

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null || event.getPackageName() == null) return;
        String pkg = event.getPackageName().toString();
        if (!pkg.equals("com.tencent.mm") && !pkg.equals("com.tencent.mobileqq")) return;

        int type = event.getEventType();
        if (type == AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED) {
            // Cache last text; for complex apps may need to traverse root for EditText
            CharSequence cs = concatEventText(event);
            if (cs != null && cs.length() > 0) {
                lastText = cs.toString();
            }
        } else if (type == AccessibilityEvent.TYPE_VIEW_CLICKED) {
            AccessibilityNodeInfo src = event.getSource();
            if (isSendButton(src)) {
                String textToSend = lastText;
                if (textToSend == null || textToSend.trim().isEmpty()) {
                    textToSend = extractTextFromRoot();
                }
                if (textToSend != null && !textToSend.trim().isEmpty()) {
                    broadcastText(pkg, textToSend.trim());
                }
            }
        }
    }

    private void broadcastText(String pkg, String text) {
        Intent i = new Intent(ACTION_SENT);
        i.putExtra("text", text);
        i.putExtra("package", pkg);
        sendBroadcast(i);
    }

    private CharSequence concatEventText(AccessibilityEvent event) {
        if (event.getText() == null) return null;
        StringBuilder sb = new StringBuilder();
        for (CharSequence c : event.getText()) {
            if (c != null) sb.append(c);
        }
        return sb.toString();
    }

    private boolean isSendButton(AccessibilityNodeInfo node) {
        if (node == null) return false;
        // Heuristics: text or content-desc contains '发送'
        CharSequence t = node.getText();
        CharSequence d = node.getContentDescription();
        if (t != null && t.toString().contains("发送")) return true;
        if (d != null && d.toString().contains("发送")) return true;
        // Could check resource-id if exposed (depends on WeChat/QQ versions)
        return false;
    }

    private String extractTextFromRoot() {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return null;
        StringBuilder sb = new StringBuilder();
        traverseForText(root, sb);
        return sb.toString();
    }

    private void traverseForText(AccessibilityNodeInfo node, StringBuilder sb) {
        if (node == null) return;
        CharSequence t = node.getText();
        if (t != null && t.length() > 0) {
            // Very naive: append all text nodes; refine to target input area only if needed
            sb.append(t).append('\n');
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            traverseForText(node.getChild(i), sb);
        }
    }

    @Override
    public void onInterrupt() {
        // No-op
    }
}
