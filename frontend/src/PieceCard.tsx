import type { Piece } from "./api";

// One piece rendered as an archival record: image + the taste attributes.
// A reusable unit — the grid maps over these, and the card owns how a piece
// presents. referrerPolicy=no-referrer helps external resale images load.
export function PieceCard({ piece }: { piece: Piece }) {
  const survives =
    piece.survives_trend === true
      ? "true"
      : piece.survives_trend === false
        ? "false"
        : "—";

  return (
    <div className="card">
      <div className="card-img">
        {piece.image_url ? (
          <img
            src={piece.image_url}
            alt={piece.name}
            loading="lazy"
            referrerPolicy="no-referrer"
            onError={(e) => (e.currentTarget.style.visibility = "hidden")}
          />
        ) : (
          <span className="no-img" />
        )}
      </div>

      <div className="card-body">
        <div className="card-name">{piece.name}</div>
        {piece.brand && <div className="card-brand">{piece.brand}</div>}

        {(piece.tension_base || piece.subverter) && (
          <div className="tension">
            <span className="k">tension</span>{" "}
            {piece.tension_base}
            {piece.subverter && (
              <>
                {" "}
                <span className="arrow">→</span> {piece.subverter}
              </>
            )}
            {piece.tension_magnitude && ` · ${piece.tension_magnitude}`}
          </div>
        )}

        <dl className="fields">
          <div><dt>role</dt><dd>{piece.role ?? "—"}</dd></div>
          <div><dt>era</dt><dd>{piece.era ?? "—"}</dd></div>
          <div><dt>provokes</dt><dd>{piece.provokes ?? "—"}</dd></div>
          <div><dt>survives</dt><dd>{survives}</dd></div>
        </dl>

        {piece.vibes.length > 0 && (
          <div className="vibes">
            {piece.vibes.slice(0, 6).map((v) => (
              <span key={v} className="vibe">{v}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
