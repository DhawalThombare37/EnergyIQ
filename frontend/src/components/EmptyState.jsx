export default function EmptyState() {
  return (
    <div className="empty-state fade-in">
      <div className="empty-icon">📂</div>
      <div className="empty-title">No Data Loaded</div>
      <div className="empty-sub">
        Use the sidebar to load the bundled dataset or upload your own CSV.
      </div>
    </div>
  )
}
