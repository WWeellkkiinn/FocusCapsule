import QtQuick
import QtQuick.Window
import QtQuick.Controls 2.15

Window {
    id: rootWin
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "transparent"
    visible: true

    property var snap: ({
        "state": "IDLE",
        "countdown": "--:--",
        "progress": 0.0,
        "settingsOpen": false,
        "draft": {
            "total_minutes": 25,
            "interval_min_minutes": 3.0,
            "interval_max_minutes": 5.0,
            "break_seconds": 10,
            "finish_break_minutes": 5,
            "sound_enabled": true
        }
    })
    property string errorText: ""
    property bool _prevSettingsOpen: false
    // scaleFactor is injected by Python (VibeBar-style softened DPI scale)
    property real sf: (typeof scaleFactor !== "undefined") ? scaleFactor : 1.0

    Connections {
        target: bridge
        function onSnapshotChanged(s) {
            var wasOpen = rootWin._prevSettingsOpen
            var nowOpen = s.settingsOpen || false
            rootWin.snap = s
            if (nowOpen && !wasOpen) {
                var d = s.draft || {}
                totalField.text      = String(d.total_minutes        !== undefined ? d.total_minutes        : 25)
                intervalMinField.text = String(d.interval_min_minutes !== undefined ? d.interval_min_minutes : 3)
                intervalMaxField.text = String(d.interval_max_minutes !== undefined ? d.interval_max_minutes : 5)
                breakField.text       = String(d.break_seconds        !== undefined ? d.break_seconds        : 10)
                finishBreakField.text = String(d.finish_break_minutes !== undefined ? d.finish_break_minutes : 5)
                soundSwitch.checked   = d.sound_enabled !== false
            }
            rootWin._prevSettingsOpen = nowOpen
        }
        function onErrorChanged(e) {
            rootWin.errorText = e
        }
    }

    // ── Main container anchored to bottom ─────────────────────────────────────
    Item {
        id: container
        anchors { bottom: parent.bottom; left: parent.left; right: parent.right }

        readonly property int barH: Math.round(20 * rootWin.sf)
        readonly property int cardH: Math.round(280 * rootWin.sf)
        readonly property int gapH: Math.round(6 * rootWin.sf)
        readonly property bool open: rootWin.snap.settingsOpen || false

        height: open ? (cardH + gapH + barH) : barH
        Behavior on height { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }

        onHeightChanged: bridge.setVisibleHeight(height)

        // ── Settings card (slides up from behind bar) ─────────────────────────
        Rectangle {
            id: settingsCard
            anchors {
                bottom: barBody.top
                bottomMargin: container.gapH
                left: parent.left
                right: parent.right
            }
            height: container.cardH
            radius: Math.round(14 * rootWin.sf)
            color: "#1A1D26"
            border { width: 1; color: "#2D3348" }
            opacity: container.open ? 1.0 : 0.0
            Behavior on opacity { NumberAnimation { duration: 200 } }
            clip: true

            Column {
                anchors {
                    fill: parent
                    topMargin: Math.round(14 * rootWin.sf)
                    leftMargin: Math.round(14 * rootWin.sf)
                    rightMargin: Math.round(14 * rootWin.sf)
                    bottomMargin: Math.round(10 * rootWin.sf)
                }
                spacing: Math.round(8 * rootWin.sf)

                // Row: 专注时长
                Row {
                    spacing: 8
                    height: 30
                    Text {
                        text: "专注时长"
                        color: "#9AA3B5"; font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                        width: 56
                    }
                    TextField {
                        id: totalField
                        width: 60; height: 28
                        color: "#E8EEFF"
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        background: Rectangle { color: "#252A3D"; radius: 6; border { width: 1; color: "#3D4560" } }
                        onEditingFinished: rootWin.errorText = ""
                    }
                    Text {
                        text: "分"
                        color: "#9AA3B5"; font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                // Row: 休息间隔
                Row {
                    spacing: 8
                    height: 30
                    Text {
                        text: "休息间隔"
                        color: "#9AA3B5"; font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                        width: 56
                    }
                    TextField {
                        id: intervalMinField
                        width: 50; height: 28
                        color: "#E8EEFF"; font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        background: Rectangle { color: "#252A3D"; radius: 6; border { width: 1; color: "#3D4560" } }
                        onEditingFinished: rootWin.errorText = ""
                    }
                    Text {
                        text: "~"
                        color: "#9AA3B5"; font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    TextField {
                        id: intervalMaxField
                        width: 50; height: 28
                        color: "#E8EEFF"; font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        background: Rectangle { color: "#252A3D"; radius: 6; border { width: 1; color: "#3D4560" } }
                        onEditingFinished: rootWin.errorText = ""
                    }
                    Text {
                        text: "分"
                        color: "#9AA3B5"; font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                // Row: 微休息时长
                Row {
                    spacing: 8
                    height: 30
                    Text {
                        text: "微休息"
                        color: "#9AA3B5"; font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                        width: 56
                    }
                    TextField {
                        id: breakField
                        width: 60; height: 28
                        color: "#E8EEFF"; font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        background: Rectangle { color: "#252A3D"; radius: 6; border { width: 1; color: "#3D4560" } }
                        onEditingFinished: rootWin.errorText = ""
                    }
                    Text {
                        text: "秒"
                        color: "#9AA3B5"; font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                // Row: 完成后休息
                Row {
                    spacing: 8
                    height: 30
                    Text {
                        text: "完成休息"
                        color: "#9AA3B5"; font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                        width: 56
                    }
                    TextField {
                        id: finishBreakField
                        width: 60; height: 28
                        color: "#E8EEFF"; font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        background: Rectangle { color: "#252A3D"; radius: 6; border { width: 1; color: "#3D4560" } }
                        onEditingFinished: rootWin.errorText = ""
                    }
                    Text {
                        text: "分"
                        color: "#9AA3B5"; font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                // Row: 声音
                Row {
                    spacing: 8
                    height: 30
                    Text {
                        text: "声音提示"
                        color: "#9AA3B5"; font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                        width: 56
                    }
                    Switch {
                        id: soundSwitch
                        checked: true
                        scale: 0.85
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                // Error message
                Text {
                    id: errorLabel
                    visible: rootWin.errorText !== ""
                    text: rootWin.errorText
                    color: "#EF4444"
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                    width: parent.width
                }

                // Buttons
                Row {
                    spacing: 8

                    Rectangle {
                        width: 76; height: 30; radius: 8
                        color: startArea.containsMouse ? "#2563EB" : "#3B82F6"
                        Behavior on color { ColorAnimation { duration: 120 } }
                        Text {
                            anchors.centerIn: parent
                            text: rootWin.snap.state === "IDLE" || rootWin.snap.state === "FINISHED" ? "开始" : "重启"
                            color: "white"; font { pixelSize: 13; bold: true }
                        }
                        MouseArea {
                            id: startArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                bridge.startWithDraft({
                                    "total_minutes":         totalField.text,
                                    "interval_min_minutes":  intervalMinField.text,
                                    "interval_max_minutes":  intervalMaxField.text,
                                    "break_seconds":         breakField.text,
                                    "finish_break_minutes":  finishBreakField.text,
                                    "sound_enabled":         soundSwitch.checked
                                })
                            }
                        }
                    }

                    Rectangle {
                        width: 56; height: 30; radius: 8
                        visible: rootWin.snap.state !== "IDLE" && rootWin.snap.state !== "FINISHED"
                        color: endArea.containsMouse ? "#4B5563" : "#374151"
                        Behavior on color { ColorAnimation { duration: 120 } }
                        Text {
                            anchors.centerIn: parent
                            text: "结束"
                            color: "#D1D5DB"; font.pixelSize: 13
                        }
                        MouseArea {
                            id: endArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: bridge.endSession()
                        }
                    }
                }
            }
        }

        // ── Progress bar (always at bottom) ──────────────────────────────────
        Rectangle {
            id: barBody
            anchors { bottom: parent.bottom; left: parent.left; right: parent.right }
            height: container.barH
            radius: Math.round(10 * rootWin.sf)
            color: "#15171D"
            border { width: 1; color: "#263041" }

            // Progress fill
            Rectangle {
                id: progressFill
                readonly property int pad: Math.round(3 * rootWin.sf)
                anchors { left: parent.left; leftMargin: pad; verticalCenter: parent.verticalCenter }
                height: parent.height - pad * 2
                width: {
                    var p = rootWin.snap.progress || 0.0
                    return Math.max(0, (barBody.width - pad * 2) * Math.min(1.0, p))
                }
                Behavior on width { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
                radius: Math.round(8 * rootWin.sf)
                color: {
                    var s = rootWin.snap.state
                    if (s === "MICRO_RESTING")  return "#F59E0B"
                    if (s === "FINISH_RESTING") return "#F59E0B"
                    if (s === "FINISHED")       return "#10B981"
                    return "#3B82F6"
                }
                Behavior on color { ColorAnimation { duration: 200 } }
            }

            // Countdown
            Text {
                id: countdownText
                anchors { left: parent.left; leftMargin: Math.round(10 * rootWin.sf); verticalCenter: parent.verticalCenter }
                text: rootWin.snap.countdown || "--:--"
                color: "#F0F4FF"
                font { family: "Consolas"; pixelSize: Math.round(11 * rootWin.sf); bold: true }
            }

            // Status label
            Text {
                anchors {
                    left: countdownText.right; leftMargin: Math.round(7 * rootWin.sf)
                    right: parent.right; rightMargin: Math.round(8 * rootWin.sf)
                    verticalCenter: parent.verticalCenter
                }
                text: stateLabel(rootWin.snap.state)
                color: "#7A8CA0"
                font.pixelSize: Math.round(10 * rootWin.sf)
                elide: Text.ElideRight
            }

            // Right double-click → quit
            TapHandler {
                acceptedButtons: Qt.RightButton
                onDoubleTapped: bridge.quit()
            }

            // Left click/drag
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton
                preventStealing: true
                cursorShape: dragging ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                property real _startMouseX: 0
                property real _startWinX: 0
                property bool dragging: false
                property int dragThreshold: Math.round(6 * rootWin.sf)
                onPressed: function(mouse) {
                    _startMouseX = mapToGlobal(mouse.x, mouse.y).x
                    _startWinX = rootWin.x
                    dragging = false
                }
                onPositionChanged: function(mouse) {
                    var dx = mapToGlobal(mouse.x, mouse.y).x - _startMouseX
                    if (!dragging && Math.abs(dx) >= dragThreshold)
                        dragging = true
                    if (dragging)
                        bridge.moveBarX(_startWinX + dx)
                }
                onReleased: function(mouse) {
                    if (dragging) {
                        bridge.saveBarX(rootWin.x)
                    } else {
                        bridge.toggleSettings()
                    }
                }
                onCanceled: dragging = false
            }
        }
    }

    function stateLabel(s) {
        if (s === "FOCUSING")       return "专注中"
        if (s === "MICRO_RESTING")  return "微休息中"
        if (s === "FINISH_RESTING") return "结束休息中"
        if (s === "FINISHED")       return "已完成 · 右键重新开始"
        return "右键打开设置并开始"
    }
}
