<template>
   <v-expansion-panel v-if="image">
    <v-expansion-panel-header>
      <v-row no-gutters>
        <v-col>
          <v-btn text icon @click.stop="inspectImage()">
            <v-icon>mdi-file-code-outline</v-icon>
          </v-btn>
          <span v-if="image.tags.length==0">
            <v-chip color="yellow lighten-2">
              <v-icon left>mdi-alert-circle-outline</v-icon>
              No tags
            </v-chip>
          </span>
          <span>
            <v-chip color="light-green lighten-2" v-for="tag in image.tags" :key="tag" @click.stop="copyTag(tag)">{{tag}}</v-chip>
          </span>
        </v-col>
        <v-col class="d-flex align-center">
          <div>{{image.createdAt | moment('YYYY-MM-DD HH:mm')}}</div>
        </v-col>
      </v-row>
    </v-expansion-panel-header> 
    <v-expansion-panel-content>
      <v-text-field v-for="tag in image.tags" :key="tag"
          :value="pullURL(tag)" :label="'Pull '+tag" outlined readonly append-icon="mdi-lock-outline"></v-text-field>
      <v-row>
        <v-col>
          <v-text-field :value="image.createdAt | moment('YYYY-MM-DD HH:mm:ss')" label="Created" outlined readonly append-icon="mdi-lock-outline"></v-text-field>
        </v-col>
        <v-col>
          <v-text-field :value="image.createdBy" label="Created By" outlined readonly append-icon="mdi-lock-outline"></v-text-field>
        </v-col>
      </v-row>
      <v-text-field 
        v-model="image.description" 
        label="Description" 
        outlined></v-text-field>
      <v-text-field :value="image.hash" label="Hash" outlined readonly append-icon="mdi-lock-outline"></v-text-field>
      <v-text-field :value="image.size | prettyBytes()" label="Size" outlined readonly append-icon="mdi-lock-outline"></v-text-field>
      <v-row>
        <v-col>
          <v-select :value="image.uploaded" label="Uploaded" outlined readonly append-icon="mdi-lock-outline" :items="[ { value: false, text: 'No' }, { value: true, text: 'Yes' } ]"></v-select>
        </v-col>
        <v-col>
          <v-text-field :value="image.downloadCount" label="Downloads" outlined readonly append-icon="mdi-lock-outline"></v-text-field>
        </v-col>
      </v-row>
    </v-expansion-panel-content>
   </v-expansion-panel>
</template>
<script lang="ts">
import Vue from 'vue';

export default Vue.extend({
  name: 'ImageDetails',
  props: [ 'image' ],
  methods: {
    pullURL: function(tag: string): string {
      return `library://${this.image.entityName}/${this.image.collectionName}/${this.image.containerName}:${tag}`
    },
    copyTag: function(tag: string) {
      this.$copyText(this.pullURL(tag))
        .then(() => this.$store.commit('snackbar/showSuccess', "Copied to clipboard."));
    },
  }
});
</script>