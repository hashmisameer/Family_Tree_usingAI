document.getElementById('toggle-form-btn').addEventListener('click', function () {
    const form = document.getElementById('add-member-form');
    form.style.display = (form.style.display === 'block') ? 'none' : 'block';
});

// Fetch family members data from the backend and render the tree
fetch('/get_family_members')
    .then(response => response.json())
    .then(data => {
        renderFamilyTree(data);
    })
    .catch(error => console.error('Error fetching family tree data:', error));

function renderFamilyTree(treeData) {
    const width = 960, height = 500;
    d3.select("#tree-container").html(""); // Clear previous tree

    const svg = d3.select("#tree-container")
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .append("g")
        .attr("transform", "translate(50, 50)");

    const treeLayout = d3.tree().size([width - 200, height - 200]);
    const root = d3.hierarchy(treeData, d => d.children);
    treeLayout(root);

    // Draw links
    svg.selectAll(".link")
        .data(root.links())
        .enter()
        .append("line")
        .classed("link", true)
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y)
        .style("stroke", "#aaa");

    // Draw nodes
    const nodes = svg.selectAll(".node")
        .data(root.descendants())
        .enter()
        .append("g")
        .classed("node", true)
        .attr("transform", d => `translate(${d.x}, ${d.y})`);

    nodes.append("circle")
        .attr("r", 10)
        .style("fill", "#4CAF50");

    nodes.append("text")
        .attr("dy", -15)
        .attr("text-anchor", "middle")
        .text(d => d.data.name);
}

// Add Member Functionality
document.getElementById('add-member-form').addEventListener('submit', function (event) {
    event.preventDefault();

    const memberData = {
        member_name: document.getElementById('member_name').value,
        relationship: document.getElementById('relationship').value,
        parent_name: document.getElementById('parent_name').value
    };

    fetch('/member', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(memberData)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        location.reload(); // Refresh the tree
    })
    .catch(error => console.error('Error adding family member:', error));
});

// Delete Member Functionality
function deleteMember(memberId) {
    fetch(`/delete_member/${memberId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        location.reload();
    })
    .catch(error => console.error('Error deleting family member:', error));
}
