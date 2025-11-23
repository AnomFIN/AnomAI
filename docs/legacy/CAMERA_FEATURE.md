# Camera Connection Feature - UI Documentation

## Overview
This document describes the new camera connection functionality added to JugiAI.

## New "Kamera" Tab in Settings

The settings dialog (⚙ Asetukset) now includes a new **"Kamera"** tab alongside the existing tabs:
- Yleiset
- OpenAI
- Paikallinen
- Ulkoasu
- **Kamera** ← NEW

## Camera Tab Layout

### Section 1: Manual Camera Configuration (Manuaalinen kamerayhteys)

This section allows users to manually configure an IP camera connection:

```
┌─────────────────────────────────────────────────────────────┐
│ Manuaalinen kamerayhteys                                    │
│━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                               │
│ Kameran IP-osoite:    [________________________]            │
│                                                               │
│ Käyttäjätunnus:       [admin___________________]            │
│                                                               │
│ Salasana:             [************************]            │
│                                                               │
│ Portti:               [8080]                                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Fields:**
- **Kameran IP-osoite**: Text input for camera IP address (e.g., 192.168.1.100)
- **Käyttäjätunnus**: Username for camera authentication (default: "admin")
- **Salasana**: Password field (masked input) for camera authentication
- **Portti**: Spinbox for camera port (1-65535, default: 8080)

### Section 2: Automatic Camera Discovery (Automaattinen kamerahaku)

This section allows users to discover cameras on the WiFi network:

```
┌─────────────────────────────────────────────────────────────┐
│ Automaattinen kamerahaku                                    │
│━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                               │
│ Etsi kamerat WiFi-verkosta:   Valmis                        │
│                                                               │
│ ┌─────────────────────────────────────────────────────┐ ▲  │
│ │ Kamera 192.168.1.100:8080                           │ █  │
│ │ Kamera 192.168.1.101:554                            │ │  │
│ │ Kamera 192.168.1.105:8081                           │ │  │
│ │                                                       │ │  │
│ │                                                       │ │  │
│ └─────────────────────────────────────────────────────┘ ▼  │
│                                                               │
│ [Etsi kamerat]  [Käytä valittua kameraa]                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- **Status label**: Shows current discovery status ("Valmis", "Etsitään kameroita...", "Löytyi X kameraa")
- **Camera listbox**: Displays discovered cameras with their IP addresses and ports
- **Etsi kamerat button**: Initiates network scan for IP cameras
- **Käytä valittua kameraa button**: Populates manual configuration fields with selected camera

## User Workflow

### Manual Configuration Workflow
1. User opens Settings (⚙ Asetukset)
2. User clicks on "Kamera" tab
3. User enters camera IP address (e.g., 192.168.1.100)
4. User enters username (defaults to "admin")
5. User enters password
6. User adjusts port if needed (defaults to 8080)
7. User clicks "Tallenna" to save settings

### Automatic Discovery Workflow
1. User opens Settings (⚙ Asetukset)
2. User clicks on "Kamera" tab
3. User clicks "Etsi kamerat" button
4. Status changes to "Etsitään kameroita..."
5. System scans local network for cameras (ports: 80, 8080, 554, 8000, 8081)
6. Discovered cameras appear in the listbox
7. Status updates to show count: "Löytyi X kameraa"
8. User selects a camera from the list
9. User clicks "Käytä valittua kameraa"
10. Manual configuration fields are populated automatically
11. User enters credentials (username/password)
12. User clicks "Tallenna" to save settings

## Technical Implementation Details

### Configuration Storage
Camera settings are stored in `config.json`:

```json
{
  "camera_ip": "192.168.1.100",
  "camera_username": "admin",
  "camera_password": "camera_password_here",
  "camera_port": 8080,
  "discovered_cameras": [
    {
      "ip": "192.168.1.100",
      "port": 8080,
      "name": "Kamera 192.168.1.100:8080"
    }
  ]
}
```

### Network Discovery Algorithm
- Determines local network subnet from system IP
- Scans first 10 and last 10 IPs in subnet (for performance)
- Tests common camera ports: 80, 8080, 554, 8000, 8081
- Uses socket timeout of 1.5 seconds per connection attempt
- Runs discovery in background thread to avoid UI freezing
- Returns list of cameras with IP, port, and friendly name

### Security Considerations
- Password field uses masked input (`show="*"`)
- Credentials stored in config.json (user should secure file permissions)
- Network scanning only checks port connectivity, doesn't authenticate
- Discovery runs with low timeout to prevent network flooding

## Design Consistency

The camera tab follows existing JugiAI design patterns:
- Uses ttk.Frame and ttk.Label widgets matching other tabs
- Follows the "SectionTitle.TLabel" and "Subtle.TLabel" style conventions
- Uses same grid layout patterns as other settings tabs
- Maintains consistent padding and spacing (pady, padx)
- Buttons use "Toolbar.TButton" style for consistency
- Follows Finnish language UI convention (like rest of application)

## Integration with Existing Code

The camera feature integrates seamlessly:
- DEFAULT_CONFIG extended with camera fields
- Settings dialog save_and_close() function updated to save camera settings
- No changes to existing functionality
- Minimal code addition (~200 lines total)
- All existing tests continue to pass
- New tests added for camera discovery function

## Future Enhancement Possibilities

Potential future improvements:
- Live camera preview in settings
- Test connection button to verify credentials
- Support for RTSP URL format
- Multiple camera profiles
- Camera stream integration with chat
- Recording/snapshot capabilities
