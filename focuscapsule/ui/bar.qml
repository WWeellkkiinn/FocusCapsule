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
    property real sf: (typeof scaleFactor !== "undefined") ? scaleFactor : 1.0

    Connections {
        target: bridge
        function onSnapshotChanged(s) { rootWin.snap = s }
        function onErrorChanged(e)    { rootWin.errorText = e }
    }

    // ── Main container ────────────────────────────────────────────────────────
    Item {
        id: container
        anchors { bottom: parent.bottom; left: parent.left; right: parent.right }

        readonly property int barH: Math.round(20 * rootWin.sf)
        property bool open: false

        // One unified rectangle expands upward — no gap, no transparent seam
        height: mainRect.height
        onHeightChanged: bridge.setVisibleHeight(height)

        HoverHandler {
            onHoveredChanged: {
                if (hovered) {
                    leaveTimer.stop()
                    if (!container.open) {
                        var d = rootWin.snap.draft || {}
                        totalField.text       = String(d.total_minutes        !== undefined ? d.total_minutes        : 25)
                        intervalMinField.text = String(d.interval_min_minutes !== undefined ? d.interval_min_minutes : 3)
                        intervalMaxField.text = String(d.interval_max_minutes !== undefined ? d.interval_max_minutes : 5)
                        breakField.text       = String(d.break_seconds        !== undefined ? d.break_seconds        : 10)
                        finishBreakField.text = String(d.finish_break_minutes !== undefined ? d.finish_break_minutes : 5)
                        soundSwitch.checked   = d.sound_enabled !== false
                        rootWin.errorText     = ""
                    }
                    container.open = true
                } else {
                    leaveTimer.restart()
                }
            }
        }
        Timer { id: leaveTimer; interval: 400; onTriggered: container.open = false }

        // Single rounded rectangle — card + bar in one piece, clip hides overflow
        Rectangle {
            id: mainRect
            anchors { bottom: parent.bottom; left: parent.left; right: parent.right }
            // Height animates between barH and barH+cardCol.implicitHeight+padding
            readonly property int cardPad: Math.round(20 * rootWin.sf)
            height: container.open
                    ? (container.barH + cardPad + cardCol.implicitHeight)
                    : container.barH
            Behavior on height { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
            radius: Math.round(10 * rootWin.sf)
            color: "#15171D"
            border { width: 1; color: "#263041" }
            clip: true

            // ── Settings content (sits above bar area) ────────────────────────
            Column {
                id: cardCol
                anchors {
                    top: parent.top; topMargin: Math.round(10 * rootWin.sf)
                    left: parent.left; leftMargin: Math.round(12 * rootWin.sf)
                    right: parent.right; rightMargin: Math.round(12 * rootWin.sf)
                }
                spacing: Math.round(6 * rootWin.sf)
                opacity: container.open ? 1.0 : 0.0
                Behavior on opacity { NumberAnimation { duration: 180 } }

                // Row: 专注时长
                Row {
                    spacing: Math.round(6 * rootWin.sf); height: Math.round(24 * rootWin.sf)
                    Text { width: Math.round(52 * rootWin.sf); text: "专注时长"; color: "#6B7A90"; font.pixelSize: Math.round(11 * rootWin.sf); anchors.verticalCenter: parent.verticalCenter }
                    TextField {
                        id: totalField; width: Math.round(52 * rootWin.sf); height: Math.round(22 * rootWin.sf)
                        color: "#C8D0E0"; font.pixelSize: Math.round(11 * rootWin.sf); horizontalAlignment: Text.AlignHCenter
                        background: Rectangle { color: "#1E2332"; radius: Math.round(5 * rootWin.sf); border { width: 1; color: "#2D3850" } }
                        onEditingFinished: rootWin.errorText = ""
                    }
                    Text { text: "分"; color: "#6B7A90"; font.pixelSize: Math.round(11 * rootWin.sf); anchors.verticalCenter: parent.verticalCenter }
                }

                // Row: 休息间隔
                Row {
                    spacing: Math.round(4 * rootWin.sf); height: Math.round(24 * rootWin.sf)
                    Text { width: Math.round(52 * rootWin.sf); text: "休息间隔"; color: "#6B7A90"; font.pixelSize: Math.round(11 * rootWin.sf); anchors.verticalCenter: parent.verticalCenter }
                    TextField {
                        id: intervalMinField; width: Math.round(44 * rootWin.sf); height: Math.round(22 * rootWin.sf)
                        color: "#C8D0E0"; font.pixelSize: Math.round(11 * rootWin.sf); horizontalAlignment: Text.AlignHCenter
                        background: Rectangle { color: "#1E2332"; radius: Math.round(5 * rootWin.sf); border { width: 1; color: "#2D3850" } }
                        onEditingFinished: rootWin.errorText = ""
                    }
                    Text { text: "~"; color: "#6B7A90"; font.pixelSize: Math.round(11 * rootWin.sf); anchors.verticalCenter: parent.verticalCenter }
                    TextField {
                        id: intervalMaxField; width: Math.round(44 * rootWin.sf); height: Math.round(22 * rootWin.sf)
                        color: "#C8D0E0"; font.pixelSize: Math.round(11 * rootWin.sf); horizontalAlignment: Text.AlignHCenter
                        background: Rectangle { color: "#1E2332"; radius: Math.round(5 * rootWin.sf); border { width: 1; color: "#2D3850" } }
                        onEditingFinished: rootWin.errorText = ""
                    }
                    Text { text: "分"; color: "#6B7A90"; font.pixelSize: Math.round(11 * rootWin.sf); anchors.verticalCenter: parent.verticalCenter }
                }

                // Row: 微休息
                Row {
                    spacing: Math.round(6 * rootWin.sf); height: Math.round(24 * rootWin.sf)
                    Text { width: Math.round(52 * rootWin.sf); text: "微休息"; color: "#6B7A90"; font.pixelSize: Math.round(11 * rootWin.sf); anchors.verticalCenter: parent.verticalCenter }
                    TextField {
                        id: breakField; width: Math.round(52 * rootWin.sf); height: Math.round(22 * rootWin.sf)
                        color: "#C8D0E0"; font.pixelSize: Math.round(11 * rootWin.sf); horizontalAlignment: Text.AlignHCenter
                        background: Rectangle { color: "#1E2332"; radius: Math.round(5 * rootWin.sf); border { width: 1; color: "#2D3850" } }
                        onEditingFinished: rootWin.errorText = ""
                    }
                    Text { text: "秒"; color: "#6B7A90"; font.pixelSize: Math.round(11 * rootWin.sf); anchors.verticalCenter: parent.verticalCenter }
                }

                // Row: 完成休息
                Row {
                    spacing: Math.round(6 * rootWin.sf); height: Math.round(24 * rootWin.sf)
                    Text { width: Math.round(52 * rootWin.sf); text: "完成休息"; color: "#6B7A90"; font.pixelSize: Math.round(11 * rootWin.sf); anchors.verticalCenter: parent.verticalCenter }
                    TextField {
                        id: finishBreakField; width: Math.round(52 * rootWin.sf); height: Math.round(22 * rootWin.sf)
                        color: "#C8D0E0"; font.pixelSize: Math.round(11 * rootWin.sf); horizontalAlignment: Text.AlignHCenter
                        background: Rectangle { color: "#1E2332"; radius: Math.round(5 * rootWin.sf); border { width: 1; color: "#2D3850" } }
                        onEditingFinished: rootWin.errorText = ""
                    }
                    Text { text: "分"; color: "#6B7A90"; font.pixelSize: Math.round(11 * rootWin.sf); anchors.verticalCenter: parent.verticalCenter }
                }

                // Row: 声音
                Row {
                    spacing: Math.round(6 * rootWin.sf); height: Math.round(24 * rootWin.sf)
                    Text { width: Math.round(52 * rootWin.sf); text: "声音提示"; color: "#6B7A90"; font.pixelSize: Math.round(11 * rootWin.sf); anchors.verticalCenter: parent.verticalCenter }
                    Switch { id: soundSwitch; checked: true; scale: 0.72; anchors.verticalCenter: parent.verticalCenter }
                }

                // Error
                Text {
                    visible: rootWin.errorText !== ""
                    text: rootWin.errorText
                    color: "#EF4444"; font.pixelSize: Math.round(10 * rootWin.sf)
                    wrapMode: Text.WordWrap; width: parent.width
                }

                // Buttons
                Row {
                    spacing: Math.round(6 * rootWin.sf)
                    Rectangle {
                        width: Math.round(64 * rootWin.sf); height: Math.round(22 * rootWin.sf); radius: Math.round(6 * rootWin.sf)
                        color: startArea.containsMouse ? "#1D4ED8" : "#2563EB"
                        Behavior on color { ColorAnimation { duration: 100 } }
                        Text { anchors.centerIn: parent; color: "#F0F4FF"; font { pixelSize: Math.round(11 * rootWin.sf); bold: true }
                            text: (rootWin.snap.state === "IDLE" || rootWin.snap.state === "FINISHED") ? "开始" : "重启" }
                        MouseArea {
                            id: startArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: bridge.startWithDraft({
                                "total_minutes": totalField.text, "interval_min_minutes": intervalMinField.text,
                                "interval_max_minutes": intervalMaxField.text, "break_seconds": breakField.text,
                                "finish_break_minutes": finishBreakField.text, "sound_enabled": soundSwitch.checked
                            })
                        }
                    }
                    Rectangle {
                        width: Math.round(48 * rootWin.sf); height: Math.round(22 * rootWin.sf); radius: Math.round(6 * rootWin.sf)
                        visible: rootWin.snap.state !== "IDLE" && rootWin.snap.state !== "FINISHED"
                        color: endArea.containsMouse ? "#374151" : "#1F2937"
                        Behavior on color { ColorAnimation { duration: 100 } }
                        Text { anchors.centerIn: parent; text: "结束"; color: "#9CA3AF"; font.pixelSize: Math.round(11 * rootWin.sf) }
                        MouseArea { id: endArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: bridge.endSession() }
                    }
                }
            }

            // ── Progress bar (always pinned to bottom of mainRect) ────────────
            Item {
                id: barArea
                anchors { bottom: parent.bottom; left: parent.left; right: parent.right }
                height: container.barH

                Rectangle {
                    readonly property int pad: Math.round(3 * rootWin.sf)
                    anchors { left: parent.left; leftMargin: pad; verticalCenter: parent.verticalCenter }
                    height: parent.height - pad * 2
                    width: Math.max(0, (barArea.width - pad * 2) * Math.min(1.0, rootWin.snap.progress || 0.0))
                    Behavior on width { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
                    radius: Math.round(8 * rootWin.sf)
                    color: {
                        var s = rootWin.snap.state
                        if (s === "MICRO_RESTING" || s === "FINISH_RESTING") return "#F59E0B"
                        if (s === "FINISHED") return "#10B981"
                        return "#3B82F6"
                    }
                    Behavior on color { ColorAnimation { duration: 200 } }
                }

                Text {
                    id: countdownText
                    anchors { left: parent.left; leftMargin: Math.round(10 * rootWin.sf); verticalCenter: parent.verticalCenter }
                    text: rootWin.snap.countdown || "--:--"
                    color: "#F0F4FF"; font { family: "Consolas"; pixelSize: Math.round(11 * rootWin.sf); bold: true }
                }
                Text {
                    anchors { left: countdownText.right; leftMargin: Math.round(6 * rootWin.sf); right: parent.right; rightMargin: Math.round(8 * rootWin.sf); verticalCenter: parent.verticalCenter }
                    text: stateLabel(rootWin.snap.state)
                    color: "#7A8CA0"; font.pixelSize: Math.round(10 * rootWin.sf); elide: Text.ElideRight
                }

                TapHandler { acceptedButtons: Qt.RightButton; onDoubleTapped: bridge.quit() }

                MouseArea {
                    anchors.fill: parent; acceptedButtons: Qt.LeftButton; preventStealing: true
                    cursorShape: dragging ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                    property real _startMouseX: 0; property real _startWinX: 0
                    property bool dragging: false
                    property int dragThreshold: Math.round(6 * rootWin.sf)
                    onPressed:  function(m) { _startMouseX = mapToGlobal(m.x, m.y).x; _startWinX = rootWin.x; dragging = false }
                    onPositionChanged: function(m) {
                        var dx = mapToGlobal(m.x, m.y).x - _startMouseX
                        if (!dragging && Math.abs(dx) >= dragThreshold) dragging = true
                        if (dragging) bridge.moveBarX(_startWinX + dx)
                    }
                    onReleased: function(m) { if (dragging) bridge.saveBarX(rootWin.x); dragging = false }
                    onCanceled: dragging = false
                }
            }
        }
    }

    function stateLabel(s) {
        if (s === "FOCUSING")       return "专注中"
        if (s === "MICRO_RESTING")  return "微休息中"
        if (s === "FINISH_RESTING") return "结束休息中"
        if (s === "FINISHED")       return "已完成"
        return "悬停展开设置"
    }
}
