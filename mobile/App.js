import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, Button, Image, ScrollView, Alert } from 'react-native';

// 将此处替换为你电脑在局域网的 IP（手机和电脑需同一 Wi-Fi）
// Windows 下可用 PowerShell: ipconfig 查看 IPv4 地址
const API_BASE = 'http://192.168.0.100:8000';

export default function App() {
  const [text, setText] = useState('你好【安安】#开心#');
  const [img, setImg] = useState(null);
  const [loading, setLoading] = useState(false);

  const onGenerate = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg);
      }
      const data = await res.json();
      setImg(data.image_base64);
    } catch (e) {
      Alert.alert('生成失败', String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>安安的素描本 - 移动端</Text>
      <TextInput
        style={styles.input}
        value={text}
        onChangeText={setText}
        placeholder="输入文字；含 #开心# 等关键词可切换底图"
        multiline
      />
      <Button title={loading ? '生成中…' : '生成图片'} onPress={onGenerate} disabled={loading} />
      {img && (
        <Image
          source={{ uri: img }}
          resizeMode="contain"
          style={{ width: '100%', height: 500, marginTop: 16, backgroundColor: '#eee' }}
        />
      )}
      <Text style={styles.hint}>注意：将 API_BASE 改为你的电脑 IP，手机与电脑需在同一网络。</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    minHeight: 80,
    marginBottom: 12,
  },
  hint: {
    fontSize: 12,
    color: '#555',
    marginTop: 12,
  }
});
