# Daily Data Quality Report

**Generated:** 2025-10-09 21:00:01

## Database Statistics

### Source Databases
- **ESPN:** 31241 games
- **hoopR:** 28779 games

### Unified Database
- **Total games:** 31243
- **Dual-source games:** 28777
- **Games with discrepancies:** 28777

## Quality Distribution

```
High (90-100)|2|90.0
Medium (70-89)|31234|77.9
Low (<70)|7|65.0
```

## Recent Discrepancies

```
home_score|28777|HIGH
game_date|22163|HIGH
away_score|7|HIGH
```

## Source Recommendations

```
hoopR|28779
ESPN|2464
```

---

**Next Steps:**
- Review discrepancies in high-severity games
- Monitor quality score trends
- Validate new data additions

**Log File:** /Users/ryanranft/nba-simulator-aws/logs/overnight/overnight_unified_20251009_205348.log
