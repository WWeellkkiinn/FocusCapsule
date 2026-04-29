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
            "auto_next": false
        }
    })
    property string errorText: ""
    property real sf: (typeof scaleFactor !== "undefined") ? scaleFactor : 1.0

    // Shared style helpers
    readonly property int _fs:  Math.round(11 * sf)
    readonly property int _fh:  Math.round(20 * sf)   // field height
    readonly property int _fw:  Math.round(30 * sf)   // field width
    readonly property real _fp: (_fh - _fs) / 2        // field vertical padding
    readonly property int _bh:  Math.round(22 * sf)   // button height
    readonly property int _bw:  Math.round(64 * sf)   // button width
    readonly property int _sbw: Math.round(52 * sf)   // small button width
    readonly property int _br:  Math.round(6 * sf)    // button radius
    readonly property bool _autoNextOn: (snap.draft && snap.draft.auto_next) ? true : false

    component SettingField: TextField {
        width: rootWin._fw; height: rootWin._fh
        color: "#f2f4f8"
        font { pixelSize: rootWin._fs; bold: true; family: "Microsoft YaHei UI" }
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        topPadding: 0; bottomPadding: 0
        leftPadding: 0; rightPadding: 0
        background: Rectangle {
            color: "#1E2332"; radius: Math.round(5 * rootWin.sf)
            border { width: 1; color: "#2D3850" }
        }
        onEditingFinished: rootWin.errorText = ""
    }

    component SettingLabel: Text {
        color: "#f2f4f8"
        font { pixelSize: rootWin._fs; bold: true; family: "Microsoft YaHei UI" }
        height: rootWin._fh; verticalAlignment: Text.AlignVCenter
    }

    component UnitLabel: Text {
        color: "#9aa3b5"
        font { pixelSize: rootWin._fs; bold: true; family: "Microsoft YaHei UI" }
        height: rootWin._fh; verticalAlignment: Text.AlignVCenter
    }

    // Unified action button
    component ActionButton: Rectangle {
        id: _btn
        width: rootWin._bw; height: rootWin._bh; radius: rootWin._br
        property string label: ""
        property color baseColor: "#2563EB"
        property color hoverColor: Qt.darker(baseColor, 1.2)
        property bool active: false
        signal clicked()

        color: _ma.containsMouse ? hoverColor : baseColor
        Behavior on color { ColorAnimation { duration: 100 } }

        Text {
            anchors.centerIn: parent
            text: _btn.label; color: "#f2f4f8"
            font { pixelSize: rootWin._fs; bold: true; family: "Microsoft YaHei UI" }
        }
        MouseArea {
            id: _ma; anchors.fill: parent
            hoverEnabled: true; cursorShape: Qt.PointingHandCursor
            onClicked: _btn.clicked()
        }
    }

    Connections {
        target: bridge
        function onSnapshotChanged(s) { rootWin.snap = s }
        function onErrorChanged(e)    { rootWin.errorText = e }
    }

    Item {
        id: container
        anchors { bottom: parent.bottom; left: parent.left; right: parent.right }

        readonly property int barH: Math.round(20 * rootWin.sf)
        property bool open: false

        height: mainRect.height
        onHeightChanged: bridge.setVisibleHeight(height)

        TapHandler { acceptedButtons: Qt.RightButton; onDoubleTapped: bridge.quit() }

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
                        rootWin.errorText     = ""
                    }
                    container.open = true
                } else {
                    leaveTimer.restart()
                }
            }
        }
        Timer { id: leaveTimer; interval: 400; onTriggered: container.open = false }

        Rectangle {
            id: mainRect
            anchors { bottom: parent.bottom; left: parent.left; right: parent.right }
            readonly property int cardPad: Math.round(20 * rootWin.sf)
            height: container.open
                    ? (container.barH + cardPad + cardCol.implicitHeight)
                    : container.barH
            Behavior on height { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }

            color: "transparent"
            border.width: 0
            clip: true

            Rectangle {
                id: bgRect
                anchors.fill: parent
                color: "#15171D"
                readonly property real r: Math.round(10 * rootWin.sf)
                topLeftRadius: r; topRightRadius: r
                bottomLeftRadius: r; bottomRightRadius: r
            }

            // ── Settings column ──────────────────────────────────────────────
            Column {
                id: cardCol
                anchors {
                    top: parent.top; topMargin: Math.round(10 * rootWin.sf)
                    left: parent.left; leftMargin: Math.round(12 * rootWin.sf)
                    right: parent.right; rightMargin: Math.round(12 * rootWin.sf)
                }
                spacing: Math.round(6 * rootWin.sf)
                enabled: container.open
                opacity: container.open ? 1.0 : 0.0
                Behavior on opacity { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }

                // ── Row A: 专注时长 + 完成休息 ──────────────────────────────
                Row {
                    width: parent.width; height: rootWin._fh; spacing: 0
                    Item {
                        width: parent.width * 0.45; height: parent.height
                        Row {
                            spacing: Math.round(4 * rootWin.sf)
                            anchors.verticalCenter: parent.verticalCenter
                            SettingLabel { text: "专注时长" }
                            SettingField { id: totalField }
                            UnitLabel    { text: "分" }
                        }
                    }
                    Item {
                        width: parent.width * 0.55; height: parent.height
                        Row {
                            spacing: Math.round(4 * rootWin.sf)
                            anchors.verticalCenter: parent.verticalCenter
                            SettingLabel { text: "完成休息" }
                            SettingField { id: finishBreakField }
                            UnitLabel    { text: "分" }
                        }
                    }
                }

                // ── Row B: 微休息 + 休息间隔 ────────────────────────────────
                Row {
                    width: parent.width; height: rootWin._fh; spacing: 0
                    Item {
                        width: parent.width * 0.45; height: parent.height
                        Row {
                            spacing: Math.round(4 * rootWin.sf)
                            anchors.verticalCenter: parent.verticalCenter
                            SettingLabel { text: "微休息" }
                            SettingField { id: breakField }
                            UnitLabel    { text: "秒" }
                        }
                    }
                    Item {
                        width: parent.width * 0.55; height: parent.height
                        Row {
                            spacing: Math.round(3 * rootWin.sf)
                            anchors.verticalCenter: parent.verticalCenter
                            SettingLabel { text: "休息间隔" }
                            SettingField { id: intervalMinField }
                            UnitLabel    { text: "~" }
                            SettingField { id: intervalMaxField }
                            UnitLabel    { text: "分" }
                        }
                    }
                }

                // ── Error ────────────────────────────────────────────────────
                Text {
                    visible: rootWin.errorText !== ""
                    text: rootWin.errorText
                    color: "#EF4444"
                    font { pixelSize: Math.round(10 * rootWin.sf); family: "Microsoft YaHei UI" }
                    wrapMode: Text.WordWrap; width: parent.width
                }

                // ── Action buttons ───────────────────────────────────────────
                Item {
                    width: parent.width; height: rootWin._bh

                    ActionButton {
                        anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                        width: rootWin._sbw
                        label: "自动循环"
                        baseColor:  rootWin._autoNextOn ? "#10B981" : "#374151"
                        hoverColor: rootWin._autoNextOn ? "#059669" : "#1F2937"
                        onClicked: bridge.toggleAutoNext()
                    }

                    Row {
                        anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                        spacing: Math.round(6 * rootWin.sf)

                        ActionButton {
                            width: rootWin._sbw
                            visible: rootWin.snap.state !== "IDLE" && rootWin.snap.state !== "FINISHED"
                            label: rootWin.snap.state === "PAUSED" ? "继续" : "暂停"
                            baseColor:  rootWin.snap.state === "PAUSED" ? "#D97706" : "#DC2626"
                            hoverColor: rootWin.snap.state === "PAUSED" ? "#B45309" : "#B91C1C"
                            onClicked: bridge.togglePause()
                        }
                        ActionButton {
                            width: rootWin._sbw
                            visible: rootWin.snap.state !== "IDLE" && rootWin.snap.state !== "FINISHED"
                            label: "结束"
                            baseColor: "#374151"; hoverColor: "#1F2937"
                            onClicked: bridge.endSession()
                        }
                        ActionButton {
                            width: rootWin._sbw
                            label: (rootWin.snap.state === "IDLE" || rootWin.snap.state === "FINISHED") ? "开始" : "重启"
                            baseColor: "#2563EB"; hoverColor: "#1D4ED8"
                            onClicked: bridge.startWithDraft({
                                "total_minutes":        totalField.text,
                                "interval_min_minutes": intervalMinField.text,
                                "interval_max_minutes": intervalMaxField.text,
                                "break_seconds":        breakField.text,
                                "finish_break_minutes": finishBreakField.text
                            })
                        }
                    }
                }
            }

            // ── Bar area ─────────────────────────────────────────────────────
            Item {
                id: barArea
                anchors { bottom: parent.bottom; left: parent.left; right: parent.right }
                height: container.barH

                // Progress bar (behind everything)
                Rectangle {
                    readonly property int pad: Math.round(3 * rootWin.sf)
                    readonly property bool isResting: {
                        var s = rootWin.snap.state
                        var pf = rootWin.snap.paused_from || ""
                        return s === "MICRO_RESTING" || s === "FINISH_RESTING"
                            || (s === "PAUSED" && (pf === "MICRO_RESTING" || pf === "FINISH_RESTING"))
                    }
                    readonly property real trackW: barArea.width - pad * 2

                    anchors.verticalCenter: parent.verticalCenter
                    // x references animated `width` so the bar stays centered during shrink
                    x: isResting ? pad + (trackW - width) / 2 : pad
                    height: parent.height - pad * 2
                    width: Math.max(height, trackW * Math.min(1.0, rootWin.snap.progress || 0.0))
                    visible: rootWin.snap.state !== "IDLE"
                    Behavior on width { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }
                    radius: height / 2
                    color: {
                        var s = rootWin.snap.state
                        if (s === "PAUSED")                                     return "#DC2626"
                        if (s === "MICRO_RESTING" || s === "FINISH_RESTING")    return "#F59E0B"
                        if (s === "FINISHED")                                   return "#10B981"
                        return "#3B82F6"
                    }
                    Behavior on color { ColorAnimation { duration: 250 } }
                }

                // Drag handler – covers whole bar, lowest z
                MouseArea {
                    anchors.fill: parent; z: 0
                    acceptedButtons: Qt.LeftButton; preventStealing: true
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

                TapHandler { acceptedButtons: Qt.RightButton; onDoubleTapped: bridge.quit() }

                // Countdown – right-anchored, always visible
                Text {
                    anchors {
                        right: parent.right; rightMargin: Math.round(8 * rootWin.sf)
                        verticalCenter: parent.verticalCenter
                    }
                    z: 1
                    text: rootWin.snap.countdown || "--:--"
                    color: "#f2f4f8"
                    font { family: "Consolas"; pixelSize: rootWin._fs; bold: true }
                }
            }
        }
    }
}
