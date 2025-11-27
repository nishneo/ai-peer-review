import ReactMarkdown from 'react-markdown';
import './Stage3.css';

export default function Stage3({ finalResponse, aggregateRankings }) {
  if (!finalResponse) {
    return null;
  }

  // Get the winning model (first in aggregate rankings = lowest average rank = winner)
  const winningModel = aggregateRankings && aggregateRankings.length > 0 
    ? aggregateRankings[0] 
    : null;

  // Format model name for display
  const formatModelName = (model) => {
    if (!model) return 'Unknown';
    // Remove provider prefix and clean up
    const parts = model.split('/');
    return parts[parts.length - 1].replace(':free', '');
  };

  return (
    <div className="stage stage3">
      <h3 className="stage-title">Stage 3: Final Council Answer</h3>
      
      {/* Winner highlight */}
      {winningModel && (
        <div className="winner-banner">
          <span className="winner-icon">🏆</span>
          <div className="winner-info">
            <span className="winner-label">Top Ranked Response</span>
            <span className="winner-model">{formatModelName(winningModel.model)}</span>
            <span className="winner-score">Avg. Rank: {winningModel.average_rank}</span>
          </div>
        </div>
      )}

      <div className="final-response">
        <div className="synthesizer-label">
          Synthesized by: {formatModelName(finalResponse.model)}
        </div>
        <div className="final-text markdown-content">
          <ReactMarkdown>{finalResponse.response}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
