import json
from pathlib import Path
from typing import Dict, List

from main import DryRunCopyBot
from utils.data_loader import DataLoader


def run_one_csv(file_path: Path) -> Dict:
    bot = DryRunCopyBot()
    trades = bot.data_loader.load_trades_from_csv(str(file_path))
    bot.total_rows_loaded = len(trades)
    print(f'TRADER_FILE {file_path.name}')
    print(f'TOTAL_ROWS_LOADED {len(trades)}')
    bot.process_trades(trades)
    bot.monitor_positions()
    summary = bot.position_manager.report()
    summary['trader_file'] = file_path.name
    summary['total_imported_rows'] = bot.total_rows_loaded
    summary['buy_candidates'] = bot.buy_candidates
    summary['ignored_trades'] = bot.ignored_trades
    summary['closed_positions_count'] = bot.closed_positions_count
    print(json.dumps(summary))
    return summary


def main():
    loader = DataLoader()
    csv_files = loader.list_csv_files()
    print(f'IMPORTS_DIR {loader.imports_dir.resolve()}')
    print('CSV_FILES')
    for file_path in csv_files:
        print(str(file_path))
    if not csv_files:
        print('NO_DATA csv_files_not_found')
        return

    results: List[Dict] = []
    for file_path in csv_files:
        print('=' * 80)
        results.append(run_one_csv(file_path))

    ranked = sorted(results, key=lambda x: (x.get('total_pnl', 0), x.get('roi', 0)), reverse=True)
    print('=' * 80)
    print('RANKING')
    for idx, row in enumerate(ranked, 1):
        print(json.dumps({
            'rank': idx,
            'trader_file': row['trader_file'],
            'total_pnl': row['total_pnl'],
            'roi': row['roi'],
            'closed_trades': row['closed_trades'],
            'buy_candidates': row['buy_candidates'],
            'ignored_trades': row['ignored_trades'],
            'max_drawdown': row['max_drawdown'],
        }))


if __name__ == '__main__':
    main()
